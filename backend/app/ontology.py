"""Ontologiya: kod daraxti, farqlovchilar va huquqiy izohlar.

Bu modul ATAYLAB "ahmoq": u faqat YAML'ni o'qiydi va tuzilmaga soladi.
Hech qanday tasnif mantiqi yo'q — u 2-bosqichdagi dvigatelda.

Muhim tamoyil: huquqiy asos matni FAQAT shu yerdagi `LegalNote.text` dan
olinadi. Tizimning boshqa hech bir joyi asos matnini yozmaydi, shakllantirmaydi
yoki tahrirlamaydi.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

OFFICIAL = "official"
UNVERIFIED = "unverified"


class LegalNote(BaseModel):
    """Rasmiy izoh yoki sarlavha matni — iqtibos manbai.

    `status` halollik mexanizmi: `unverified` bo'lsa, matn rasmiy manbadan
    tasdiqlanmagan va UI'da ogohlantirish bilan ko'rsatiladi.
    """

    id: str
    ref: str  # masalan: "61-bobga izoh, 1-band"
    text: str
    status: str = UNVERIFIED
    # Matn qayerdan olingan / qayerdan tasdiqlash kerak. `unverified`
    # yozuvlarni tekshirish ishini aniq maqsadli qiladi: har bir matn
    # uchun "qaysi hujjatning qaysi joyiga qarash kerak" yozib qo'yiladi.
    # Batafsil manba ro'yxati: data/VERIFICATION.md
    source_hint: str = ""


class AttributeDef(BaseModel):
    """Tasnif uchun kerakli xususiyat va uning YOPIQ qiymatlar to'plami.

    Yopiqlik muhim: ekstraktor faqat shu qiymatlardan birini qaytara oladi,
    aks holda qiymat `None` ga aylanadi va tizim jim turadi.
    """

    name: str
    label_uz: str
    question_uz: str
    values: list[str]
    # Qiymat -> odam o'qiydigan matn. UI tugmalarida `koylak_bluzka` emas,
    # "Ko'ylak yoki bluzka" ko'rinishi kerak. Yorliqlar shu yerda turadi,
    # frontendda emas: yangi qiymat qo'shilganda uni tarjimasiz qoldirib
    # bo'lmasligi test bilan ta'minlanadi.
    value_labels: dict[str, str] = Field(default_factory=dict)
    hint_uz: str = ""


class Node(BaseModel):
    """Daraxt tuguni: bo'lim, bob, pozitsiya yoki yakuniy 10-xonali kod."""

    code: str
    level: str  # ildiz | bolim | bob | guruh | pozitsiya | yakuniy
    title_uz: str
    parent: str | None = None
    is_final: bool = False
    duty_rate: float | None = None
    note_ids: list[str] = Field(default_factory=list)
    status: str = UNVERIFIED


class Discriminator(BaseModel):
    """Bitta tugunda javob talab qiladigan farqlovchi savol.

    Agar `attribute` qiymati noma'lum bo'lsa — dvigatel shu yerda TO'XTAYDI.
    """

    id: str
    at_node: str
    attribute: str
    why_uz: str  # nega bu savol muhim (boj stavkasiga ta'siri)
    branches: dict[str, str]  # atribut qiymati -> farzand node kodi
    basis: list[str]  # LegalNote id lari


class Ontology(BaseModel):
    root: str
    nodes: dict[str, Node]
    discriminators: list[Discriminator]
    attributes: dict[str, AttributeDef]
    notes: dict[str, LegalNote]

    def discriminators_at(self, code: str) -> list[Discriminator]:
        return [d for d in self.discriminators if d.at_node == code]

    def children(self, code: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.parent == code]

    def note(self, note_id: str) -> LegalNote:
        """Izohni id bo'yicha oladi.

        Mavjud bo'lmasa KeyError ko'taradi — bu ataylab: asos matni
        "topilmadi" holatida jimgina bo'sh qolmasligi kerak.
        """
        return self.notes[note_id]


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def load_ontology(data_dir: str | None = None) -> Ontology:
    base = Path(data_dir) if data_dir else DATA_DIR

    raw_attrs = _load_yaml(base / "attributes.yaml")
    attributes = {
        nom: AttributeDef(name=nom, **body) for nom, body in raw_attrs.items()
    }

    raw_notes = _load_yaml(base / "notes.yaml")
    notes = {nid: LegalNote(id=nid, **body) for nid, body in raw_notes.items()}

    raw_nodes = _load_yaml(base / "nodes.yaml")
    nodes = {n["code"]: Node(**n) for n in raw_nodes}

    raw_discs = _load_yaml(base / "discriminators.yaml")
    discriminators = [Discriminator(**d) for d in raw_discs]

    root = next(kod for kod, n in nodes.items() if n.parent is None)

    return Ontology(
        root=root,
        nodes=nodes,
        discriminators=discriminators,
        attributes=attributes,
        notes=notes,
    )
