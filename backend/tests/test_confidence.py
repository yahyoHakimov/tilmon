"""4-bosqich (davomi): Ishonch darajasi.

Ishonch — bezak emas. Agar tizim atributni foydalanuvchi matnidan
XULOSA QILGAN bo'lsa (masalan "futbolka" -> demak trikotaj), buni
aytishi shart. Foydalanuvchi o'sha xulosani tekshirib ko'rishi kerak.

Qoida sodda: yo'ldagi barcha atributlar bevosita aytilgan bo'lsa —
"yuqori". Hech bo'lmaganda bittasi xulosa bo'lsa — "orta".
"""

import json

import pytest

from app.confidence import assess
from app.engine import classify
from app.extractor import extract
from app.ontology import load_ontology


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


class FakeClient:
    def __init__(self, javob):
        self.javob = javob

    def complete(self, system, user):
        return self.javob


def qur(onto, **manbalar):
    """Berilgan source'lar bilan to'liq bluzka ekstraksiyasini yasaydi."""
    qiymatlar = {
        "mahsulot_kategoriyasi": "kiyim",
        "mato_turi": "trikotaj",
        "mahsulot_turi": "koylak_bluzka",
        "jins": "ayol",
        "tarkib": "paxta",
    }
    atributlar = {
        nom: {"value": qiymat, "source": manbalar.get(nom, "stated")}
        for nom, qiymat in qiymatlar.items()
    }
    return extract(
        "bluzka", onto, FakeClient(json.dumps({"attributes": atributlar}))
    )


def test_barcha_atributlar_stated_bolsa_yuqori(onto):
    n = qur(onto)
    i = assess(classify(n.as_dict(), onto), n)
    assert i.level == "yuqori"
    assert i.inferred_attributes == []


def test_bitta_inferred_bolsa_orta(onto):
    n = qur(onto, mato_turi="inferred")
    i = assess(classify(n.as_dict(), onto), n)
    assert i.level == "orta"
    assert i.inferred_attributes == ["mato_turi"]


def test_bir_nechta_inferred_hammasi_royxatda(onto):
    n = qur(onto, mato_turi="inferred", jins="inferred")
    i = assess(classify(n.as_dict(), onto), n)
    assert i.level == "orta"
    assert set(i.inferred_attributes) == {"mato_turi", "jins"}


def test_yoldan_tashqari_inferred_ishonchni_tushirmaydi(onto):
    """"uzun yeng" xulosa qilingan bo'lsa ham, u kodga ta'sir qilmagan.

    Faqat tasnifda ISHLATILGAN atributlar hisobga olinadi.
    """
    n = extract(
        "bluzka",
        onto,
        FakeClient(
            json.dumps(
                {
                    "attributes": {
                        "mahsulot_kategoriyasi": {"value": "kiyim", "source": "stated"},
                        "mato_turi": {"value": "trikotaj", "source": "stated"},
                        "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated"},
                        "jins": {"value": "ayol", "source": "stated"},
                        "tarkib": {"value": "paxta", "source": "stated"},
                        "kabel_turi": {"value": "konnektorli", "source": "inferred"},
                    }
                }
            )
        ),
    )
    natija = classify(n.as_dict(), onto)
    assert "kabel_turi" in natija.unused_attributes
    assert assess(natija, n).level == "yuqori"


def test_insufficient_uchun_ishonch_yoq(onto):
    """Kod berilmasa, ishonch tushunchasi ma'nosiz."""
    n = qur(onto)
    toliqmas = classify({k: v for k, v in n.as_dict().items() if k != "mato_turi"}, onto)
    assert assess(toliqmas, n) is None


def test_model_ishlamasa_ishonch_yoq(onto):
    n = extract("bluzka", onto, FakeClient("buzuq"))
    assert assess(classify(n.as_dict(), onto), n) is None
