"""Tasnif dvigateli — sof deterministik, modelsiz.

Kirish: atributlar lug'ati. Chiqish: Resolved yoki Insufficient.

Butun mantiq bitta oddiy siklda: ildizdan boshlab daraxt bo'ylab pastga
tushamiz. Har tugunda farqlovchi bor — uning atributi kiritmada bo'lsa,
tegishli tarmoqqa o'tamiz; bo'lmasa — TO'XTAYMIZ.

Kod bu yerda o'ylab topilmaydi: har bir qadam ontologiyadagi mavjud
tarmoqqa ergashadi, oxirgi tugun esa `is_final` bo'lishi shart.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.ontology import Ontology, load_ontology

# Nega to'xtadik
KORSATILMAGAN = "korsatilmagan"  # atribut umuman berilmagan
NOTANISH_QIYMAT = "notanish_qiymat"  # atribut bor, lekin qiymati daraxtda yo'q


class Step(BaseModel):
    """Yo'ldagi bitta qadam — keyinchalik asos zanjiriga aylanadi."""

    node: str
    discriminator: str
    attribute: str
    value: str
    target: str


class RejectedBranch(BaseModel):
    """Ko'rib chiqilgan, lekin rad etilgan tarmoq va rad etish sababi."""

    code: str
    title_uz: str
    discriminator: str
    attribute: str
    required_value: str  # bu tarmoq talab qilgan qiymat
    actual_value: str  # kiritmadagi haqiqiy qiymat


class Candidate(BaseModel):
    """Atribut noma'lum bo'lganda — mumkin bo'lgan variantlardan biri.

    Qolgan ma'lum atributlar bilan iloji boricha chuqurlashtiriladi, shunda
    foydalanuvchi "6106 yoki 6206" emas, "6106 10 000 0 yoki 6206 30 000 0"
    ni ko'radi.
    """

    branch_value: str
    label_uz: str  # UI tugmasi uchun: "Trikotaj — ip halqalaridan..."
    code: str
    title_uz: str
    is_final: bool


class Resolved(BaseModel):
    status: Literal["resolved"] = "resolved"
    code: str
    title_uz: str
    duty_rate: float | None
    path: list[Step]
    rejected: list[RejectedBranch]
    used_attributes: list[str]
    unused_attributes: list[str]


class Insufficient(BaseModel):
    """Kod bera olmadik.

    Diqqat: bu sinfda `code` maydoni ATAYLAB yo'q. `natija.code` yozgan
    har qanday kod darhol AttributeError bilan yiqiladi va jimgina
    `None` ni deklaratsiyaga olib bormaydi.
    """

    status: Literal["insufficient"] = "insufficient"
    stopped_at: str
    stopped_at_title_uz: str
    missing_attribute: str
    reason: Literal["korsatilmagan", "notanish_qiymat"]
    provided_value: str | None
    question_uz: str
    hint_uz: str
    why_uz: str
    candidates: list[Candidate]
    path: list[Step]
    rejected: list[RejectedBranch]
    used_attributes: list[str]
    unused_attributes: list[str]


def _walk(
    boshlangich: str, atributlar: dict[str, str], onto: Ontology
) -> tuple[str, list[Step], list[RejectedBranch]]:
    """Daraxt bo'ylab imkon qadar pastga tushadi.

    Qaytaradi: (to'xtagan tugun, bosib o'tilgan qadamlar, rad etilganlar).
    To'xtash sababi chaqiruvchi tomonidan aniqlanadi — bu funksiya
    faqat "qayergacha bora oldik" degan savolga javob beradi.
    """
    joriy = boshlangich
    qadamlar: list[Step] = []
    rad: list[RejectedBranch] = []

    while True:
        farqlovchilar = onto.discriminators_at(joriy)
        if not farqlovchilar:
            return joriy, qadamlar, rad

        d = farqlovchilar[0]
        qiymat = atributlar.get(d.attribute)
        if qiymat is None or qiymat not in d.branches:
            return joriy, qadamlar, rad

        for tarmoq_qiymati, target in d.branches.items():
            if tarmoq_qiymati == qiymat:
                continue
            rad.append(
                RejectedBranch(
                    code=target,
                    title_uz=onto.nodes[target].title_uz,
                    discriminator=d.id,
                    attribute=d.attribute,
                    required_value=tarmoq_qiymati,
                    actual_value=qiymat,
                )
            )

        target = d.branches[qiymat]
        qadamlar.append(
            Step(
                node=joriy,
                discriminator=d.id,
                attribute=d.attribute,
                value=qiymat,
                target=target,
            )
        )
        joriy = target


def _candidates(
    node: str, atributlar: dict[str, str], onto: Ontology
) -> list[Candidate]:
    """To'xtash nuqtasidagi har bir tarmoq uchun eng aniq mumkin bo'lgan kod.

    Har bir tarmoqdan qolgan atributlar bilan pastga tushib ko'ramiz.
    Chuqurroq tusha olsak — foydalanuvchi aniqroq xavfni ko'radi.
    """
    farqlovchilar = onto.discriminators_at(node)
    if not farqlovchilar:
        return []

    d = farqlovchilar[0]
    yorliqlar = onto.attributes[d.attribute].value_labels
    nomzodlar = []
    for tarmoq_qiymati, target in d.branches.items():
        yakuniy, _, _ = _walk(target, atributlar, onto)
        n = onto.nodes[yakuniy]
        nomzodlar.append(
            Candidate(
                branch_value=tarmoq_qiymati,
                label_uz=yorliqlar[tarmoq_qiymati],
                code=n.code,
                title_uz=n.title_uz,
                is_final=n.is_final,
            )
        )
    return nomzodlar


def classify(atributlar: dict[str, str], onto: Ontology | None = None):
    """Atributlardan yakuniy kodni aniqlaydi yoki nima yetishmayotganini aytadi."""
    onto = onto or load_ontology()

    toxtagan, qadamlar, rad = _walk(onto.root, atributlar, onto)
    node = onto.nodes[toxtagan]

    ishlatilgan = [q.attribute for q in qadamlar]
    ishlatilmagan = [k for k in atributlar if k not in ishlatilgan]

    if node.is_final:
        return Resolved(
            code=node.code,
            title_uz=node.title_uz,
            duty_rate=node.duty_rate,
            path=qadamlar,
            rejected=rad,
            used_attributes=ishlatilgan,
            unused_attributes=ishlatilmagan,
        )

    # Yakuniy emas — demak farqlovchi bor, lekin javob bera olmadik.
    # (Boshi berk tugun bo'lishi mumkin emas: ontologiya testi buni kafolatlaydi.)
    d = onto.discriminators_at(toxtagan)[0]
    berilgan = atributlar.get(d.attribute)
    atr = onto.attributes[d.attribute]

    # Atribut ro'yxatdan chiqarilgan qiymatlar orasida bo'lmasa ham
    # "notanish" hisoblanadi: shu tugunda u tarmoqqa olib bormaydi.
    sabab = NOTANISH_QIYMAT if berilgan is not None else KORSATILMAGAN

    return Insufficient(
        stopped_at=toxtagan,
        stopped_at_title_uz=node.title_uz,
        missing_attribute=d.attribute,
        reason=sabab,
        provided_value=berilgan,
        question_uz=atr.question_uz,
        hint_uz=atr.hint_uz,
        why_uz=d.why_uz,
        candidates=_candidates(toxtagan, atributlar, onto),
        path=qadamlar,
        rejected=rad,
        used_attributes=ishlatilgan,
        unused_attributes=ishlatilmagan,
    )
