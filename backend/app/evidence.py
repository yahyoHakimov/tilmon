"""Asos zanjiri — "Nega bu kod?" savoliga javob.

Bu modulning yagona qoidasi: HUQUQIY MATN BU YERDA YOZILMAYDI.

Har bir iqtibos `ontology.notes` dan `id` bo'yicha olinadi va o'zgarishsiz
uzatiladi. Bu yerda f-string, `.format()`, qisqartirish yoki "tushunarli
qilib qayta yozish" yo'q va bo'lmasligi kerak — test buni tekshiradi.

Shu sababli bu modul juda qisqa. U ataylab shunday.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.engine import Insufficient, Resolved
from app.ontology import UNVERIFIED, Ontology


class Citation(BaseModel):
    """Rasmiy matndan o'zgarishsiz iqtibos."""

    note_id: str
    ref: str
    text: str
    status: str


class EvidenceStep(BaseModel):
    """Yo'ldagi bitta qadam va uni oqlaydigan matnlar."""

    node: str
    node_title_uz: str
    attribute: str
    attribute_label_uz: str
    value: str
    target: str
    target_title_uz: str
    why_uz: str
    citations: list[Citation]


class RejectionEvidence(BaseModel):
    """Rad etilgan tarmoq va rad etish asosi."""

    code: str
    title_uz: str
    attribute: str
    required_value: str
    actual_value: str
    citations: list[Citation]


class Evidence(BaseModel):
    steps: list[EvidenceStep]
    rejections: list[RejectionEvidence]
    has_unverified: bool
    unverified_note_ids: list[str]


def _cite(note_ids: list[str], onto: Ontology) -> list[Citation]:
    """Izohlarni id bo'yicha oladi. Matn shu yerda O'ZGARTIRILMAYDI.

    Takrorlarni tartibni saqlagan holda olib tashlaydi.
    """
    korilgan: set[str] = set()
    iqtiboslar = []
    for nid in note_ids:
        if nid in korilgan:
            continue
        korilgan.add(nid)
        n = onto.note(nid)  # yo'q bo'lsa KeyError — jimgina o'tib ketmaydi
        iqtiboslar.append(
            Citation(note_id=n.id, ref=n.ref, text=n.text, status=n.status)
        )
    return iqtiboslar


def _discriminator(disc_id: str, onto: Ontology):
    return next(d for d in onto.discriminators if d.id == disc_id)


def build_evidence(natija: Resolved | Insufficient, onto: Ontology) -> Evidence:
    """Tasnif natijasidan to'liq asos zanjirini yig'adi.

    Resolved va Insufficient uchun bir xil ishlaydi: to'liqmas holatda
    zanjir qisqaroq bo'ladi, lekin foydalanuvchi qayergacha borganini
    va nima uchun to'xtaganini ko'radi.
    """
    qadamlar = []
    for q in natija.path:
        d = _discriminator(q.discriminator, onto)
        node = onto.nodes[q.node]
        target = onto.nodes[q.target]
        qadamlar.append(
            EvidenceStep(
                node=node.code,
                node_title_uz=node.title_uz,
                attribute=q.attribute,
                attribute_label_uz=onto.attributes[q.attribute].label_uz,
                value=q.value,
                target=target.code,
                target_title_uz=target.title_uz,
                why_uz=d.why_uz,
                # Farqlovchining asosi + maqsad tugunning o'z izohlari
                citations=_cite(d.basis + target.note_ids, onto),
            )
        )

    rad = []
    for r in natija.rejected:
        d = _discriminator(r.discriminator, onto)
        rad.append(
            RejectionEvidence(
                code=r.code,
                title_uz=r.title_uz,
                attribute=r.attribute,
                required_value=r.required_value,
                actual_value=r.actual_value,
                citations=_cite(d.basis + onto.nodes[r.code].note_ids, onto),
            )
        )

    tasdiqlanmagan = []
    for guruh in (qadamlar, rad):
        for element in guruh:
            for c in element.citations:
                if c.status == UNVERIFIED and c.note_id not in tasdiqlanmagan:
                    tasdiqlanmagan.append(c.note_id)

    return Evidence(
        steps=qadamlar,
        rejections=rad,
        has_unverified=bool(tasdiqlanmagan),
        unverified_note_ids=tasdiqlanmagan,
    )
