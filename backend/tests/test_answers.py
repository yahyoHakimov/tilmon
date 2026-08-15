"""8-bosqich: Savol-javob sikli.

Tizim "mato turi ko'rsatilmagan" deb aytishi yetarli emas — foydalanuvchi
javob berib, to'xtagan joydan davom eta olishi kerak.

Ikkita muhim qoida:

1. Javob ham YOPIQ ro'yxatdan bo'lishi shart. Bu yerda modelga qo'yilgan
   talab foydalanuvchiga ham qo'yiladi: erkin matn qabul qilinmaydi.
   Farqi shundaki, noto'g'ri javob jimgina tashlanmaydi — 422 qaytariladi.
   Sabab: javob bizning UI'mizdan keladi, noto'g'ri qiymat mijoz xatosi.

2. Javob ekstraktsiyadan USTUN turadi, lekin ziddiyat yashirilmaydi.
   Agar matnda "to'qima" deyilgan bo'lsa-yu, foydalanuvchi "trikotaj"
   deb javob bersa — tizim javobni oladi, ammo ziddiyatni ko'rsatadi.
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.answers import merge_answers
from app.api import app, get_client
from app.api_auth import joriy_foydalanuvchi
from app.throttle import tozala_urinishlar
from app.engine import Insufficient, Resolved, classify
from app.extractor import ANSWERED, STATED, extract
from app.ontology import load_ontology

TOZA = {
    "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred"},
    "mato_turi": {"value": "trikotaj", "source": "stated"},
    "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated"},
    "jins": {"value": "ayol", "source": "stated"},
    "tarkib": {"value": "paxta", "source": "stated"},
}
MATOSIZ = {k: v for k, v in TOZA.items() if k != "mato_turi"}


class FakeClient:
    """Atributlarni to'g'ri JSON o'ramida qaytaradi."""

    def __init__(self, atributlar):
        self.atributlar = atributlar

    def complete(self, system, user):
        return json.dumps({"attributes": self.atributlar})


class RawClient:
    """Xom matnni o'zgartirmasdan qaytaradi — nosoz javobni taqlid qilish uchun."""

    def __init__(self, xom):
        self.xom = xom

    def complete(self, system, user):
        return self.xom


# --- Auth chetlab o'tish ----------------------------------------------------
#
# Bu fayldagi testlar TASNIF KONTRAKTINI sinaydi, kirish tizimini emas.
# `/api/classify` endi auth talab qiladi, lekin bu yerda bog'liqlikni
# soxta foydalanuvchi bilan almashtiramiz — shunda testlar Postgres'siz
# ham ishlashda davom etadi va yadro infratuzilmasiz sinaladi.
#
# Auth'ning o'zi `test_authz.py` da haqiqiy baza bilan sinaladi.


class SoxtaUser:
    """`joriy_foydalanuvchi` qaytaradigan minimal obyekt."""

    id = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
    email = "test@example.uz"
    role = "user"
    is_active = True


def _auth_chetlab_ot():
    app.dependency_overrides[joriy_foydalanuvchi] = SoxtaUser
    tozala_urinishlar()


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


def ajrat(onto, atributlar):
    return extract("bluzka", onto, FakeClient(atributlar))


def mijoz(atributlar):
    app.dependency_overrides[get_client] = lambda: FakeClient(atributlar)
    _auth_chetlab_ot()
    return TestClient(app)


@pytest.fixture(autouse=True)
def tozala():
    yield
    app.dependency_overrides.clear()


# --- Birlashtirish mantiqi -------------------------------------------------


def test_javob_atributga_aylanadi(onto):
    birlashgan, _ = merge_answers(ajrat(onto, MATOSIZ), {"mato_turi": "trikotaj"}, onto)
    assert birlashgan.as_dict()["mato_turi"] == "trikotaj"


def test_javob_manbai_answered(onto):
    """Javob "aytilgan" emas, "javob berilgan" — bu farq saqlanishi kerak."""
    birlashgan, _ = merge_answers(ajrat(onto, MATOSIZ), {"mato_turi": "trikotaj"}, onto)
    assert birlashgan.attributes["mato_turi"].source == ANSWERED


def test_javob_ekstraktsiyadan_ustun(onto):
    birlashgan, _ = merge_answers(ajrat(onto, TOZA), {"mato_turi": "toqima"}, onto)
    assert birlashgan.as_dict()["mato_turi"] == "toqima"


def test_ziddiyat_yashirilmaydi(onto):
    """⭐ Foydalanuvchi o'z matnini bekor qilganini ko'rishi kerak."""
    _, ziddiyatlar = merge_answers(ajrat(onto, TOZA), {"mato_turi": "toqima"}, onto)
    assert len(ziddiyatlar) == 1
    z = ziddiyatlar[0]
    assert z.attribute == "mato_turi"
    assert z.extracted_value == "trikotaj"
    assert z.answered_value == "toqima"


def test_bir_xil_qiymat_ziddiyat_emas(onto):
    _, ziddiyatlar = merge_answers(ajrat(onto, TOZA), {"mato_turi": "trikotaj"}, onto)
    assert ziddiyatlar == []


def test_bosh_javoblar_ekstraktsiyani_ozgartirmaydi(onto):
    asos = ajrat(onto, TOZA)
    birlashgan, ziddiyatlar = merge_answers(asos, {}, onto)
    assert birlashgan.as_dict() == asos.as_dict()
    assert ziddiyatlar == []


def test_notanish_atribut_xato_koradi(onto):
    with pytest.raises(ValueError, match="mahsulot_rangi"):
        merge_answers(ajrat(onto, MATOSIZ), {"mahsulot_rangi": "qizil"}, onto)


def test_notanish_qiymat_xato_koradi(onto):
    """⭐ Javob jimgina tashlanmaydi — model javobidan farqi shu."""
    with pytest.raises(ValueError, match="bambuk"):
        merge_answers(ajrat(onto, MATOSIZ), {"tarkib": "bambuk"}, onto)


def test_javob_normallashtiriladi(onto):
    birlashgan, _ = merge_answers(ajrat(onto, MATOSIZ), {"mato_turi": " TRIKOTAJ "}, onto)
    assert birlashgan.as_dict()["mato_turi"] == "trikotaj"


# --- ⭐ To'liq sikl: savoldan kodgacha -------------------------------------


def test_bitta_javob_bilan_kod_aniqlanadi(onto):
    """Matnda hamma narsa bor edi, faqat mato turi yo'q — bitta javob yetarli."""
    birlashgan, _ = merge_answers(ajrat(onto, MATOSIZ), {"mato_turi": "trikotaj"}, onto)
    natija = classify(birlashgan.as_dict(), onto)
    assert isinstance(natija, Resolved)
    assert natija.code == "6106 10 000 0"


def test_ikki_bosqichli_sikl(onto):
    """«ayollar bluzkasi» -> savol -> javob -> yana savol -> javob -> kod."""
    faqat_bluzka = {
        "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred"},
        "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated"},
        "jins": {"value": "ayol", "source": "stated"},
    }
    ajratma = ajrat(onto, faqat_bluzka)

    # 1-qadam: mato turi so'raladi
    n1 = classify(ajratma.as_dict(), onto)
    assert isinstance(n1, Insufficient)
    assert n1.missing_attribute == "mato_turi"

    # 2-qadam: javob berdik, endi tarkib so'raladi
    b2, _ = merge_answers(ajratma, {"mato_turi": "trikotaj"}, onto)
    n2 = classify(b2.as_dict(), onto)
    assert isinstance(n2, Insufficient)
    assert n2.missing_attribute == "tarkib"

    # 3-qadam: ikkinchi javob -> kod
    b3, _ = merge_answers(ajratma, {"mato_turi": "trikotaj", "tarkib": "paxta"}, onto)
    n3 = classify(b3.as_dict(), onto)
    assert isinstance(n3, Resolved)
    assert n3.code == "6106 10 000 0"


def test_javoblar_ishonchni_tushirmaydi(onto):
    """Foydalanuvchi o'zi aytgan qiymat xulosa emas."""
    from app.confidence import assess

    birlashgan, _ = merge_answers(ajrat(onto, MATOSIZ), {"mato_turi": "trikotaj"}, onto)
    natija = classify(birlashgan.as_dict(), onto)
    ishonch = assess(natija, birlashgan)
    assert "mato_turi" not in ishonch.inferred_attributes


def test_model_ishlamasa_ham_javoblar_bilan_kod_aniqlanadi(onto):
    """⭐ Model butunlay yiqilsa ham, foydalanuvchi qo'lda javob berib
    kodni aniqlay oladi. Tizim modelga bog'lanib qolmaydi."""
    yiqilgan = extract("bluzka", onto, RawClient("bu JSON emas"))
    assert not yiqilgan.model_ok
    assert yiqilgan.as_dict() == {}

    birlashgan, _ = merge_answers(
        yiqilgan,
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mato_turi": "trikotaj",
            "mahsulot_turi": "koylak_bluzka",
            "jins": "ayol",
            "tarkib": "paxta",
        },
        onto,
    )
    natija = classify(birlashgan.as_dict(), onto)
    assert isinstance(natija, Resolved)
    assert natija.code == "6106 10 000 0"


# --- Nomzodlar javob variantlari sifatida ----------------------------------


def test_nomzodlar_ozbekcha_yorliqqa_ega(onto):
    """UI tugmada `koylak_bluzka` emas, odam o'qiydigan matn ko'rsatishi kerak."""
    natija = classify(ajrat(onto, MATOSIZ).as_dict(), onto)
    for c in natija.candidates:
        assert c.label_uz.strip()
        assert c.label_uz != c.branch_value


def test_nomzod_yorliqlari_ontologiyadan(onto):
    natija = classify(ajrat(onto, MATOSIZ).as_dict(), onto)
    yorliqlar = onto.attributes["mato_turi"].value_labels
    for c in natija.candidates:
        assert c.label_uz == yorliqlar[c.branch_value]


# --- HTTP kontrakti --------------------------------------------------------


def test_api_javob_qabul_qiladi():
    r = mijoz(MATOSIZ).post(
        "/api/classify",
        json={"text": "ayollar bluzkasi", "answers": {"mato_turi": "trikotaj"}},
    )
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "resolved"
    assert b["code"] == "6106 10 000 0"


def test_api_javobsiz_avvalgidek_ishlaydi():
    r = mijoz(MATOSIZ).post("/api/classify", json={"text": "ayollar bluzkasi"})
    assert r.status_code == 200
    assert r.json()["status"] == "insufficient"


def test_api_notogri_javob_qiymati_422():
    r = mijoz(MATOSIZ).post(
        "/api/classify",
        json={"text": "ayollar bluzkasi", "answers": {"mato_turi": "bambuk"}},
    )
    assert r.status_code == 422


def test_api_notanish_javob_atributi_422():
    r = mijoz(MATOSIZ).post(
        "/api/classify",
        json={"text": "ayollar bluzkasi", "answers": {"rang": "qizil"}},
    )
    assert r.status_code == 422


def test_api_ziddiyatni_javobda_koradi():
    r = mijoz(TOZA).post(
        "/api/classify",
        json={"text": "trikotaj bluzka", "answers": {"mato_turi": "toqima"}},
    )
    b = r.json()
    assert b["code"] == "6206 30 000 0"
    assert len(b["conflicts"]) == 1
    assert b["conflicts"][0]["attribute"] == "mato_turi"


def test_api_javob_manbai_korinadi():
    b = mijoz(MATOSIZ).post(
        "/api/classify",
        json={"text": "ayollar bluzkasi", "answers": {"mato_turi": "trikotaj"}},
    ).json()
    a = next(a for a in b["attributes"] if a["name"] == "mato_turi")
    assert a["source"] == ANSWERED


def test_api_ekstraktsiya_manbalari_ozgarmaydi():
    b = mijoz(MATOSIZ).post(
        "/api/classify",
        json={"text": "ayollar bluzkasi", "answers": {"mato_turi": "trikotaj"}},
    ).json()
    a = next(a for a in b["attributes"] if a["name"] == "jins")
    assert a["source"] == STATED
