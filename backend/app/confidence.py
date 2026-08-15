"""Ishonch darajasi.

Bezak emas. Agar tizim atributni foydalanuvchi matnidan XULOSA QILGAN
bo'lsa, buni aytishi shart — foydalanuvchi o'sha xulosani tekshirishi
kerak.

Qoida ataylab sodda va tushunarli: yo'lda ishlatilgan barcha atributlar
bevosita aytilgan bo'lsa — "yuqori". Hech bo'lmaganda bittasi xulosa
bo'lsa — "orta".

"past" darajasi YO'Q. Agar ishonch pastligi kod berishga to'sqinlik
qiladigan darajada bo'lsa, dvigatel allaqachon jim turgan bo'ladi.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.engine import Insufficient, Resolved
from app.extractor import INFERRED, Extraction


class Confidence(BaseModel):
    level: Literal["yuqori", "orta"]
    inferred_attributes: list[str]


def assess(
    natija: Resolved | Insufficient, ajratma: Extraction
) -> Confidence | None:
    """Ishonch darajasini hisoblaydi. Kod berilmagan bo'lsa — None.

    Faqat tasnifda ISHLATILGAN atributlar hisobga olinadi: yo'ldan
    tashqaridagi xulosa kodga ta'sir qilmagan, demak ishonchni
    tushirmaydi.
    """
    if not isinstance(natija, Resolved):
        return None

    xulosalar = [
        q.attribute
        for q in natija.path
        if ajratma.attributes.get(q.attribute)
        and ajratma.attributes[q.attribute].source == INFERRED
    ]
    return Confidence(
        level="orta" if xulosalar else "yuqori",
        inferred_attributes=xulosalar,
    )
