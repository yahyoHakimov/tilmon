"""Foydalanuvchi javoblarini ekstraktsiya bilan birlashtiradi.

Tizim "mato turi ko'rsatilmagan" deb aytishi yetarli emas — foydalanuvchi
javob berib, to'xtagan joydan davom eta olishi kerak.

Ikkita qoida bu modulni belgilaydi:

1. Javob ham YOPIQ ro'yxatdan bo'lishi shart — modelga qo'yilgan talab
   foydalanuvchiga ham qo'yiladi. Lekin noto'g'ri javob JIMGINA
   TASHLANMAYDI, `ValueError` ko'tariladi. Farqning sababi manbada:
   model javobi ishonchsiz kanal, foydalanuvchi javobi esa bizning
   UI'mizdan keladi va u faqat mavjud variantlarni taklif qiladi.
   Noto'g'ri qiymat kelishi — mijoz xatosi, uni yashirish mumkin emas.

2. Javob ekstraktsiyadan ustun turadi, lekin ziddiyat yashirilmaydi.
   Matnda "to'qima" deyilgan bo'lsa-yu, foydalanuvchi "trikotaj" deb
   javob bersa — javob olinadi, ammo ziddiyat javobga qo'shiladi.
   Foydalanuvchi o'z matnini bekor qilganini bilishi kerak.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.extractor import ANSWERED, ExtractedAttribute, Extraction
from app.ontology import Ontology

JAVOB_ASOSI = "foydalanuvchi javobi"


class Conflict(BaseModel):
    """Matndan ajratilgan qiymat foydalanuvchi javobiga zid kelgan holat."""

    attribute: str
    extracted_value: str
    answered_value: str


def merge_answers(
    ajratma: Extraction, javoblar: dict[str, str], onto: Ontology
) -> tuple[Extraction, list[Conflict]]:
    """Javoblarni ekstraktsiya ustiga qo'yadi.

    Raises:
        ValueError: atribut yoki qiymat ontologiyada e'lon qilinmagan bo'lsa.
    """
    if not javoblar:
        return ajratma, []

    atributlar = dict(ajratma.attributes)
    ziddiyatlar: list[Conflict] = []

    for nom, xom in javoblar.items():
        if nom not in onto.attributes:
            raise ValueError(f"noma'lum xususiyat: {nom}")

        qiymat = str(xom).strip().lower()
        if qiymat not in onto.attributes[nom].values:
            raise ValueError(
                f"'{nom}' uchun noto'g'ri qiymat: {xom}. "
                f"Ruxsat etilgan: {', '.join(onto.attributes[nom].values)}"
            )

        avvalgi = atributlar.get(nom)
        if avvalgi is not None and avvalgi.value != qiymat:
            ziddiyatlar.append(
                Conflict(
                    attribute=nom,
                    extracted_value=avvalgi.value,
                    answered_value=qiymat,
                )
            )

        atributlar[nom] = ExtractedAttribute(
            name=nom, value=qiymat, source=ANSWERED, evidence_uz=JAVOB_ASOSI
        )

    return (
        ajratma.model_copy(update={"attributes": atributlar}),
        ziddiyatlar,
    )
