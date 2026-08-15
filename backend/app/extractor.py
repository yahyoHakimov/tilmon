"""Atribut ekstraktori — modelning tizimga YAGONA kirish nuqtasi.

Bu modulning butun mazmuni bitta jumlada: MODELGA ISHONILMAYDI.

Model qaytargan har bir narsa ontologiyaning yopiq qiymatlar to'plamiga
solishtiriladi. Mos kelmagani `dropped` ro'yxatiga tushadi va tasnifga
umuman yetib bormaydi. Model kod taklif qilsa — biz uni o'qimaymiz ham.

Shu sababli modelning har qanday nosozligi (buzuq JSON, timeout,
o'ylab topilgan qiymat, kod taklifi) bir xil natija beradi: kamroq
atribut, demak dvigatel jim turadi. Noto'g'ri kod emas.
"""

from __future__ import annotations

import json
from typing import Literal, Protocol

from pydantic import BaseModel

from app.ontology import Ontology, load_ontology

STATED = "stated"  # foydalanuvchi matnda bevosita aytgan
INFERRED = "inferred"  # matndan mantiqan kelib chiqadi (model xulosasi)
ANSWERED = "answered"  # tizim savoliga foydalanuvchi javob berdi

# Model qaytarishi mumkin, lekin biz butunlay e'tiborsiz qoldiradigan
# kalitlar. Ro'yxat hujjat sifatida: bular ataylab o'qilmaydi.
EUTIBORSIZ_KALITLAR = frozenset(
    {"code", "hs_code", "tn_ved", "tnved", "codes", "confidence", "reasoning", "rationale"}
)


class LLMClient(Protocol):
    """Model bilan aloqaning eng kichik shartnomasi.

    Ataylab minimal: testlarda oson taqlid qilinadi, provayder almashsa
    faqat shu interfeys implementatsiyasi o'zgaradi.
    """

    def complete(self, system: str, user: str) -> str: ...


class ExtractedAttribute(BaseModel):
    name: str
    value: str
    # "answered" ni faqat `answers.merge_answers` qo'yadi — model uni
    # hech qachon qaytara olmaydi (sanitayzer `stated`/`inferred` dan
    # boshqasini `inferred` ga aylantiradi).
    source: Literal["stated", "inferred", "answered"]
    evidence_uz: str = ""


class DroppedValue(BaseModel):
    """Model qaytargan, lekin qabul qilinmagan qiymat.

    Ro'yxat shaffoflik uchun: modelning nimani o'ylab topganini ko'rish
    mumkin. Bu qiymatlar tasnifga YETIB BORMAYDI.
    """

    name: str
    value: str | None
    reason: str


class Extraction(BaseModel):
    attributes: dict[str, ExtractedAttribute] = {}
    dropped: list[DroppedValue] = []
    model_ok: bool = True
    error: str | None = None

    def as_dict(self) -> dict[str, str]:
        """Dvigatel uchun sof atribut lug'ati."""
        return {nom: a.value for nom, a in self.attributes.items()}


def build_system_prompt(onto: Ontology) -> str:
    """Prompt ONTOLOGIYADAN hosil qilinadi, qo'lda yozilmaydi.

    Shunda YAML'ga yangi atribut yoki qiymat qo'shilsa, prompt o'zi
    yangilanadi va ikkisi bir-biridan ajralib ketmaydi.
    """
    satrlar = [
        "Siz bojxona tasnifi uchun MA'LUMOT AJRATUVCHISIZ.",
        "",
        "Vazifangiz: foydalanuvchi matnidan quyidagi xususiyatlarni ajratib olish.",
        "",
        "Siz TN VED kodini AYTMAYSIZ va tasnifni O'ZINGIZ QILMAYSIZ. Kodni",
        "boshqa tizim, rasmiy tasnif qoidalari asosida aniqlaydi. Javobingizga",
        "kod, bob raqami yoki tasnif izohi yozmang — ular o'qilmaydi.",
        "",
        "QAT'IY QOIDALAR:",
        "1. Har bir xususiyat uchun FAQAT quyida ko'rsatilgan qiymatlardan",
        "   birini tanlang. Boshqa so'z yozish taqiqlanadi.",
        "2. Matnda aytilmagan yoki ishonchsiz xususiyatni JAVOBGA KIRITMANG.",
        "   Taxmin qilish taqiqlanadi. Bilmaslik — to'g'ri javob.",
        "3. \"source\" maydoni:",
        f"   \"{STATED}\"   — foydalanuvchi bevosita aytgan",
        f"   \"{INFERRED}\" — matndan mantiqan kelib chiqadi",
        "4. \"evidence\" — foydalanuvchi matnidan aynan qaysi so'zlar asos bo'ldi.",
        "",
        "XUSUSIYATLAR:",
    ]
    for nom, atr in onto.attributes.items():
        satrlar.append(f"  {nom} — {atr.label_uz}")
        satrlar.append(f"    ruxsat etilgan qiymatlar: {', '.join(atr.values)}")

    satrlar += [
        "",
        "JAVOB SHAKLI (faqat JSON):",
        '{"attributes": {"<xususiyat>": {"value": "<qiymat>",',
        f'  "source": "{STATED}|{INFERRED}", "evidence": "<foydalanuvchi so\'zlari>"}}}}',
        "",
        "Hech qanday xususiyat aniq bo'lmasa: {\"attributes\": {}}",
    ]
    return "\n".join(satrlar)


def _parse(xom: str) -> dict | None:
    """Model javobini lug'atga aylantiradi. Muvaffaqiyatsiz bo'lsa None."""
    try:
        yuklangan = json.loads(xom)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(yuklangan, dict):
        return None

    # `attributes` o'rami bo'lsa — undan, bo'lmasa ildizdan o'qiymiz.
    ichki = yuklangan.get("attributes")
    if isinstance(ichki, dict):
        return ichki
    if "attributes" in yuklangan:
        # Kaliti bor, lekin lug'at emas (null, ro'yxat) — bo'sh hisoblanadi.
        return {}
    return yuklangan


def _sanitize(xom_atributlar: dict, onto: Ontology) -> tuple[dict, list[DroppedValue]]:
    """Modelning javobini ontologiyaga solishtirib filtrlaydi.

    Bu funksiya tizimning himoya devori. Undan o'tgan har bir qiymat
    ontologiyada e'lon qilingan bo'lishi kafolatlanadi.
    """
    qabul: dict[str, ExtractedAttribute] = {}
    tashlangan: list[DroppedValue] = []

    for nom, xom in xom_atributlar.items():
        if nom in EUTIBORSIZ_KALITLAR:
            continue  # kod, reasoning va h.k. — umuman o'qilmaydi

        if nom not in onto.attributes:
            tashlangan.append(
                DroppedValue(
                    name=nom,
                    value=str(xom) if xom is not None else None,
                    reason="ontologiyada bunday xususiyat yo'q",
                )
            )
            continue

        # Model {"value": ..., "source": ...} yoki to'g'ridan-to'g'ri
        # string qaytarishi mumkin — ikkisini ham qabul qilamiz.
        if isinstance(xom, dict):
            qiymat = xom.get("value")
            manba = xom.get("source")
            asos = xom.get("evidence") or ""
        else:
            qiymat, manba, asos = xom, None, ""

        if not isinstance(qiymat, str) or not qiymat.strip():
            tashlangan.append(
                DroppedValue(name=nom, value=None, reason="qiymat bo'sh yoki matn emas")
            )
            continue

        normal = qiymat.strip().lower()
        if normal not in onto.attributes[nom].values:
            tashlangan.append(
                DroppedValue(
                    name=nom,
                    value=qiymat,
                    reason="qiymat ruxsat etilgan ro'yxatda yo'q",
                )
            )
            continue

        # Noaniq `source` — ehtiyotkorlik tomon: kamroq ishonch.
        qabul[nom] = ExtractedAttribute(
            name=nom,
            value=normal,
            source=STATED if manba == STATED else INFERRED,
            evidence_uz=asos if isinstance(asos, str) else "",
        )

    return qabul, tashlangan


def extract(
    matn: str, onto: Ontology | None = None, client: LLMClient | None = None
) -> Extraction:
    """Erkin matndan atributlarni ajratadi.

    Model chaqirilmasa yoki nosoz javob bersa, natija bo'sh bo'ladi —
    va bo'sh natija dvigatelni jim turishga majbur qiladi. Xato holatida
    ham tizim taxmin qilmaydi.
    """
    onto = onto or load_ontology()

    if not matn or not matn.strip():
        return Extraction(model_ok=True)

    if client is None:
        from app.llm import default_client

        client = default_client()

    try:
        xom = client.complete(build_system_prompt(onto), matn.strip())
    except Exception as e:  # noqa: BLE001 — har qanday nosozlik bir xil natija
        return Extraction(model_ok=False, error=f"{type(e).__name__}: {e}")

    ajratilgan = _parse(xom)
    if ajratilgan is None:
        return Extraction(model_ok=False, error="model javobi JSON emas")

    qabul, tashlangan = _sanitize(ajratilgan, onto)
    return Extraction(attributes=qabul, dropped=tashlangan, model_ok=True)
