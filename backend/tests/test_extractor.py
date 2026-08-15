"""4-bosqich: Atribut ekstraktori.

Bu yagona joy — modelning tizimga kirish nuqtasi. Shuning uchun eng ko'p
test shu yerda.

Asosiy g'oya: model ISHONILMAYDI. U qaytargan hamma narsa ontologiyaning
yopiq qiymatlar to'plamiga solishtiriladi. Mos kelmagani tashlanadi.
Model butunlay buzilsa ham (buzuq JSON, timeout, kod qaytarish) tizim
noto'g'ri kod bermasligi kerak — faqat jim turishi kerak.

FakeClient tufayli bu testlar OpenAI kalitisiz ishlaydi.
"""

import json

import pytest

from app.engine import Insufficient, Resolved, classify
from app.extractor import build_system_prompt, extract
from app.ontology import load_ontology


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


class FakeClient:
    """Modelni taqlid qiladi. `javob` Exception bo'lsa — ko'taradi."""

    def __init__(self, javob):
        self.javob = javob
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if isinstance(self.javob, Exception):
            raise self.javob
        return self.javob


def fake(atributlar: dict, **qoshimcha) -> FakeClient:
    return FakeClient(json.dumps({"attributes": atributlar, **qoshimcha}))


TOZA_BLUZKA = {
    "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred", "evidence": "bluzka"},
    "mato_turi": {"value": "trikotaj", "source": "stated", "evidence": "trikotaj"},
    "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated", "evidence": "bluzkasi"},
    "jins": {"value": "ayol", "source": "stated", "evidence": "ayollar"},
    "tarkib": {"value": "paxta", "source": "stated", "evidence": "100% paxta"},
}


# --- Normal ish -------------------------------------------------------------


def test_toza_javob_atributlarga_aylanadi(onto):
    n = extract("ayollar bluzkasi, 100% paxta, trikotaj", onto, fake(TOZA_BLUZKA))
    assert n.as_dict() == {
        "mahsulot_kategoriyasi": "kiyim",
        "mato_turi": "trikotaj",
        "mahsulot_turi": "koylak_bluzka",
        "jins": "ayol",
        "tarkib": "paxta",
    }
    assert n.model_ok is True


def test_source_stated_va_inferred_farqlanadi(onto):
    n = extract("ayollar bluzkasi, paxta, trikotaj", onto, fake(TOZA_BLUZKA))
    assert n.attributes["mato_turi"].source == "stated"
    assert n.attributes["mahsulot_kategoriyasi"].source == "inferred"


def test_foydalanuvchi_sozlari_saqlanadi(onto):
    """Foydalanuvchi "nega shunday tushundingiz?" deb so'rashi mumkin."""
    n = extract("ayollar bluzkasi", onto, fake(TOZA_BLUZKA))
    assert n.attributes["jins"].evidence_uz == "ayollar"


# --- ⭐ Modelga ishonmaslik -------------------------------------------------


def test_sxemadan_tashqari_atribut_tashlanadi(onto):
    n = extract(
        "bluzka",
        onto,
        fake({**TOZA_BLUZKA, "rang": {"value": "qizil", "source": "stated"}}),
    )
    assert "rang" not in n.as_dict()
    assert "rang" in [d.name for d in n.dropped]


def test_sxemadan_tashqari_qiymat_tashlanadi(onto):
    """Model "bambuk" desa — bu qiymat ontologiyada yo'q, ishlatilmaydi."""
    buzuq = {**TOZA_BLUZKA, "tarkib": {"value": "bambuk", "source": "stated"}}
    n = extract("bambukdan bluzka", onto, fake(buzuq))
    assert "tarkib" not in n.as_dict()
    tashlangan = next(d for d in n.dropped if d.name == "tarkib")
    assert tashlangan.value == "bambuk"


def test_model_kod_qaytarsa_eutiborsiz_qoldiriladi(onto):
    """⭐⭐ Model kod taklif qilsa ham, tizim uni O'QIMAYDI.

    Kod faqat dvigatel tomonidan, ontologiya bo'ylab yurish natijasida
    hosil bo'ladi. Modelning "6106 10 000 0" degan gapi shovqin.
    """
    client = fake(
        TOZA_BLUZKA,
        code="6106 10 000 0",
        hs_code="6106",
        tn_ved="6206 30 000 0",
        confidence="yuqori",
        reasoning="61-bob trikotaj kiyimlarni qamraydi",
    )
    n = extract("ayollar bluzkasi", onto, client)
    seriya = n.model_dump_json()
    assert "6106" not in seriya
    assert "6206" not in seriya
    assert "61-bob" not in seriya


def test_kod_attributes_ICHIDA_kelsa_ham_eutiborsiz(onto):
    """⭐ Model kodni xususiyatlar ichiga yashirishi mumkin.

    Modeldan javob shakli kafolatlanmaydi — u `code` ni `attributes`
    yonida ham, ichida ham qaytarishi mumkin. Ikkalasi ham o'qilmasligi
    kerak.
    """
    n = extract(
        "ayollar bluzkasi",
        onto,
        fake(
            {
                **TOZA_BLUZKA,
                "code": {"value": "6106 10 000 0", "source": "stated"},
                "hs_code": "6206",
                "reasoning": "61-bob trikotaj kiyimlarni qamraydi",
                "confidence": "yuqori",
            }
        ),
    )
    seriya = n.model_dump_json()
    assert "6106" not in seriya, "kod javobga sizib o'tdi"
    assert "6206" not in seriya
    assert "61-bob" not in seriya
    # `dropped` ro'yxatiga ham tushmasligi kerak: bu shovqin, xato emas.
    assert [d.name for d in n.dropped] == []


def test_null_qiymat_tashlanadi(onto):
    n = extract(
        "bluzka", onto, fake({**TOZA_BLUZKA, "mato_turi": {"value": None, "source": "stated"}})
    )
    assert "mato_turi" not in n.as_dict()


def test_bosh_qiymat_tashlanadi(onto):
    n = extract(
        "bluzka", onto, fake({**TOZA_BLUZKA, "mato_turi": {"value": "", "source": "stated"}})
    )
    assert "mato_turi" not in n.as_dict()


def test_qiymat_normallashtiriladi(onto):
    """Yopiq ro'yxatga solishtirganda bo'sh joy va registr muhim emas."""
    n = extract(
        "bluzka",
        onto,
        fake({**TOZA_BLUZKA, "mato_turi": {"value": "  TRIKOTAJ ", "source": "stated"}}),
    )
    assert n.as_dict()["mato_turi"] == "trikotaj"


def test_notogri_source_ehtiyotkorlik_bilan_inferred_boladi(onto):
    """Ishonchsiz holatda kamroq ishonch — ko'proq emas."""
    n = extract(
        "bluzka",
        onto,
        fake({**TOZA_BLUZKA, "jins": {"value": "ayol", "source": "aniq"}}),
    )
    assert n.attributes["jins"].source == "inferred"


def test_source_yoq_bolsa_inferred(onto):
    n = extract("bluzka", onto, fake({"jins": {"value": "ayol"}}))
    assert n.attributes["jins"].source == "inferred"


def test_qiymat_ozi_string_bolsa_ham_qabul_qilinadi(onto):
    """Model sxemani sodda qaytarsa ham ishlashi kerak: {"jins": "ayol"}."""
    n = extract("bluzka", onto, fake({"jins": "ayol"}))
    assert n.as_dict() == {"jins": "ayol"}
    assert n.attributes["jins"].source == "inferred"


# --- ⭐ Model buzilganda ----------------------------------------------------


def test_buzuq_json_bosh_natija_beradi(onto):
    n = extract("bluzka", onto, FakeClient("bu JSON emas, shunchaki matn"))
    assert n.as_dict() == {}
    assert n.model_ok is False


def test_json_lekin_notogri_shakl(onto):
    n = extract("bluzka", onto, FakeClient('["a", "b"]'))
    assert n.as_dict() == {}
    assert n.model_ok is False


def test_attributes_kaliti_yoq_bolsa_ildizdan_oqiladi(onto):
    """Model o'ramsiz qaytarsa ham ishlaydi."""
    n = extract("bluzka", onto, FakeClient(json.dumps({"jins": "ayol"})))
    assert n.as_dict() == {"jins": "ayol"}


def test_client_xato_bersa_bosh_natija(onto):
    n = extract("bluzka", onto, FakeClient(TimeoutError("timeout")))
    assert n.as_dict() == {}
    assert n.model_ok is False
    assert n.error is not None


def test_bosh_matn_modelga_murojaat_qilmaydi(onto):
    client = fake(TOZA_BLUZKA)
    n = extract("   ", onto, client)
    assert n.as_dict() == {}
    assert client.calls == [], "bo'sh matn uchun model chaqirilmasligi kerak"


# --- Prompt ontologiyadan generatsiya qilinadi ------------------------------


def test_prompt_barcha_atribut_va_qiymatlarni_oz_ichiga_oladi(onto):
    """Prompt qo'lda yozilmaydi — ontologiyadan hosil qilinadi.

    Shunda YAML'ga yangi qiymat qo'shilsa, prompt avtomatik yangilanadi
    va ikkisi bir-biridan ajralib ketmaydi.
    """
    prompt = build_system_prompt(onto)
    for nom, atr in onto.attributes.items():
        assert nom in prompt
        for qiymat in atr.values:
            assert qiymat in prompt


def test_prompt_taxmin_qilishni_taqiqlaydi(onto):
    prompt = build_system_prompt(onto).lower()
    assert "taxmin" in prompt


def test_prompt_kod_aytishni_taqiqlaydi(onto):
    prompt = build_system_prompt(onto).lower()
    assert "kod" in prompt


# --- Dvigatel bilan birga (integratsiya) -----------------------------------


def test_ekstraktordan_dvigatelga_toliq_yol(onto):
    n = extract("ayollar bluzkasi, 100% paxta, trikotaj", onto, fake(TOZA_BLUZKA))
    natija = classify(n.as_dict(), onto)
    assert isinstance(natija, Resolved)
    assert natija.code == "6106 10 000 0"


def test_mato_turi_yoq_bolsa_toliq_yolda_ham_kod_yoq(onto):
    """⭐ Uchidan uchiga: "ayollar bluzkasi" -> kod yo'q."""
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    n = extract("ayollar bluzkasi", onto, fake(qismli))
    natija = classify(n.as_dict(), onto)
    assert isinstance(natija, Insufficient)
    assert natija.missing_attribute == "mato_turi"


@pytest.mark.parametrize(
    "buzuq_javob",
    [
        "shunchaki matn",
        "{}",
        '{"attributes": {}}',
        '{"attributes": null}',
        '{"code": "6106 10 000 0"}',
        '{"attributes": {"mato_turi": {"value": "bambuk"}}}',
        "null",
        "",
    ],
)
def test_model_buzilganda_hech_qachon_kod_berilmaydi(buzuq_javob, onto):
    """⭐⭐ Modelning har qanday nosozligida tizim jim turadi."""
    n = extract("ayollar bluzkasi", onto, FakeClient(buzuq_javob))
    assert isinstance(classify(n.as_dict(), onto), Insufficient)
