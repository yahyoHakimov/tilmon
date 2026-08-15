"""5-bosqich: HTTP API kontrakti.

Bu qatlam yangi mantiq qo'shmaydi — u faqat 1-4 bosqichlarni birlashtiradi
va HTTP orqali chiqaradi. Shuning uchun testlar KONTRAKTGA qaratilgan:
javob shakli, xato holatlari va — eng muhimi — kod maydonining
to'liqmas javobda MAVJUD EMASLIGI.
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import app, get_client
from app.api_auth import joriy_foydalanuvchi
from app.throttle import tozala_urinishlar

TOZA_BLUZKA = {
    "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred", "evidence": "bluzka"},
    "mato_turi": {"value": "trikotaj", "source": "stated", "evidence": "trikotaj"},
    "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated", "evidence": "bluzka"},
    "jins": {"value": "ayol", "source": "stated", "evidence": "ayollar"},
    "tarkib": {"value": "paxta", "source": "stated", "evidence": "paxta"},
}


class FakeClient:
    def __init__(self, javob):
        self.javob = javob

    def complete(self, system, user):
        if isinstance(self.javob, Exception):
            raise self.javob
        return self.javob


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


def mijoz(atributlar=None, **qoshimcha):
    """Berilgan atributlarni qaytaradigan soxta model bilan TestClient."""
    javob = json.dumps({"attributes": atributlar or {}, **qoshimcha})
    app.dependency_overrides[get_client] = lambda: FakeClient(javob)
    _auth_chetlab_ot()
    return TestClient(app)


def mijoz_xato(xato):
    app.dependency_overrides[get_client] = lambda: FakeClient(xato)
    _auth_chetlab_ot()
    return TestClient(app)


@pytest.fixture(autouse=True)
def tozala():
    # Auth har bir test uchun chetlab o'tiladi: bu fayl tasnif
    # kontraktini sinaydi, kirish tizimini emas.
    _auth_chetlab_ot()
    yield
    app.dependency_overrides.clear()
    tozala_urinishlar()


def tasnif(client, matn="ayollar bluzkasi"):
    return client.post("/api/classify", json={"text": matn})


# --- Sog'liq va yordamchi endpointlar --------------------------------------


def test_healthz():
    r = TestClient(app).get("/api/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_healthz_ontologiya_holatini_koradi():
    """Ma'lumot yuklanmasa, servis "sog'lom" deb ko'rinmasligi kerak."""
    b = TestClient(app).get("/api/healthz").json()
    assert b["nodes"] > 0
    assert b["discriminators"] > 0


def test_attributes_endpoint_ui_uchun_sxemani_beradi():
    r = TestClient(app).get("/api/attributes")
    assert r.status_code == 200
    b = r.json()
    assert "mato_turi" in b
    assert set(b["mato_turi"]["values"]) == {"trikotaj", "toqima"}
    assert b["mato_turi"]["question_uz"].strip()


# --- Resolved javob --------------------------------------------------------


def test_resolved_javob_sxemasi():
    r = tasnif(mijoz(TOZA_BLUZKA), "ayollar bluzkasi, paxta, trikotaj")
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "resolved"
    assert b["code"] == "6106 10 000 0"
    assert b["title_uz"]
    assert b["duty_rate"] == 10.0
    assert b["confidence"]["level"] in ("yuqori", "orta")
    assert b["evidence"]["steps"]
    assert b["evidence"]["rejections"]


def test_resolved_javobda_ajratilgan_atributlar_korinadi():
    """Foydalanuvchi tizim uni QANDAY tushunganini ko'rishi kerak."""
    b = tasnif(mijoz(TOZA_BLUZKA)).json()
    nomlar = {a["name"] for a in b["attributes"]}
    assert "mato_turi" in nomlar
    a = next(a for a in b["attributes"] if a["name"] == "mato_turi")
    assert a["value"] == "trikotaj"
    assert a["source"] == "stated"


def test_resolved_javob_iqtiboslari_haqiqiy():
    from app.ontology import load_ontology

    onto = load_ontology()
    haqiqiy = {n.text for n in onto.notes.values()}
    b = tasnif(mijoz(TOZA_BLUZKA)).json()
    tekshirilgan = 0
    for q in b["evidence"]["steps"]:
        for c in q["citations"]:
            assert c["text"] in haqiqiy
            tekshirilgan += 1
    assert tekshirilgan > 0


# --- ⭐ Insufficient javob -------------------------------------------------


def test_insufficient_javob_sxemasi():
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    r = tasnif(mijoz(qismli))
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "insufficient"
    assert b["missing_attribute"] == "mato_turi"
    assert b["question_uz"].strip()
    assert b["why_uz"].strip()
    assert len(b["candidates"]) == 2


def test_insufficient_javobda_code_maydoni_UMUMAN_YOQ():
    """⭐⭐ Eng muhim API testi.

    `null` emas — maydonning O'ZI bo'lmasligi kerak. Frontend
    `data.code` yozsa, `undefined` chiqadi va ekranda hech narsa
    ko'rinmaydi. `null` bo'lsa ham shunday, lekin JSON'ni qayta
    ishlaydigan boshqa tizim uni "kod yo'q" emas, "kod bo'sh" deb
    tushunishi mumkin.
    """
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    xom = tasnif(mijoz(qismli)).json()
    assert "code" not in xom
    assert "duty_rate" not in xom
    assert "confidence" not in xom


def test_insufficient_nomzodlar_kodlari_korinadi():
    """Foydalanuvchi qaysi ikki kod o'rtasida turganini bilishi kerak."""
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    b = tasnif(mijoz(qismli)).json()
    kodlar = {c["code"] for c in b["candidates"]}
    assert kodlar == {"6106 10 000 0", "6206 30 000 0"}


def test_bosh_kirishda_ham_javob_beradi():
    b = tasnif(mijoz({}), "salom").json()
    assert b["status"] == "insufficient"
    assert "code" not in b


# --- ⭐ Model nosozligi ----------------------------------------------------


def test_model_ishlamasa_500_emas_insufficient():
    """Model yiqilsa, API 500 qaytarmasligi kerak — jim javob berishi kerak."""
    r = tasnif(mijoz_xato(TimeoutError("timeout")))
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "insufficient"
    assert b["model_ok"] is False
    assert "code" not in b


def test_api_kaliti_sozlanmagan_bolsa_ham_500_emas(monkeypatch):
    """⭐ Sozlama xatosi ham xavfsiz kechishi kerak.

    OPENAI_API_KEY yo'q bo'lsa, servis yiqilmasligi va — eng muhimi —
    kod taxmin qilmasligi kerak.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.llm import default_client

    default_client.cache_clear()

    r = TestClient(app).post("/api/classify", json={"text": "ayollar bluzkasi"})
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "insufficient"
    assert b["model_ok"] is False
    assert "code" not in b


def test_kalitsiz_muhitda_ham_notogri_sorov_422(monkeypatch):
    """Bog'liqlik so'rov tekshiruvidan oldin yiqilmasligi kerak."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = TestClient(app).post("/api/classify", json={"text": ""})
    assert r.status_code == 422


def test_model_buzuq_json_bersa_ham_kod_yoq():
    app.dependency_overrides[get_client] = lambda: FakeClient("bu JSON emas")
    b = TestClient(app).post("/api/classify", json={"text": "bluzka"}).json()
    assert b["status"] == "insufficient"
    assert "code" not in b


def test_model_kod_taklif_qilsa_javobga_tushmaydi():
    """Model kodni to'g'ridan-to'g'ri aytsa ham, u API javobiga chiqmaydi."""
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    c = mijoz(
        {**qismli, "code": "6206 30 000 0"},
        code="6106 10 000 0",
        reasoning="61-bob trikotaj kiyimlarni qamraydi",
    )
    b = tasnif(c).json()
    assert b["status"] == "insufficient"
    assert "61-bob trikotaj kiyimlarni qamraydi" not in json.dumps(b, ensure_ascii=False)


# --- Kiritmani tekshirish --------------------------------------------------


def test_bosh_matn_422():
    r = TestClient(app).post("/api/classify", json={"text": ""})
    assert r.status_code == 422


def test_faqat_probel_422():
    r = TestClient(app).post("/api/classify", json={"text": "     "})
    assert r.status_code == 422


def test_matn_maydoni_yoq_422():
    r = TestClient(app).post("/api/classify", json={})
    assert r.status_code == 422


def test_juda_uzun_matn_422():
    r = TestClient(app).post("/api/classify", json={"text": "a" * 5000})
    assert r.status_code == 422


# --- ⭐ Halollik: har doim ko'rinadigan ogohlantirishlar -------------------


@pytest.mark.parametrize("holat", ["toliq", "toliqmas"])
def test_disclaimer_har_doim_bor(holat):
    """Loyihaning talabi: "Buni yashirmang — birinchi bo'lib o'zingiz ayting"."""
    a = TOZA_BLUZKA if holat == "toliq" else {}
    b = tasnif(mijoz(a)).json()
    assert b["disclaimer_uz"].strip()
    assert "yuridik kuchga ega emas" in b["disclaimer_uz"]


@pytest.mark.parametrize("holat", ["toliq", "toliqmas", "bosh"])
def test_tasdiqlanmagan_malumot_ogohlantirishi_HAR_DOIM_bor(holat):
    """⭐ Ogohlantirish javob mazmuniga bog'liq bo'lmasligi kerak.

    Eng xavfli holat — hech narsa aniqlanmagan, lekin nomzod kodlar
    ko'rsatilgan javob. Unda iqtibos yo'q, demak iqtiboslarga bog'langan
    bayroq ko'tarilmaydi va foydalanuvchi tizim sinov ma'lumotida
    ishlayotganini bilmay qoladi.
    """
    a = {"toliq": TOZA_BLUZKA, "toliqmas": {"jins": "ayol"}, "bosh": {}}[holat]
    b = tasnif(mijoz(a)).json()
    assert b["data_warning_uz"].strip()


def test_iqtibos_bolganda_evidence_bayrogi_kotariladi():
    """`evidence.has_unverified` esa aynan JAVOBDAGI iqtiboslarga tegishli."""
    b = tasnif(mijoz(TOZA_BLUZKA)).json()
    assert b["evidence"]["has_unverified"] is True
    assert b["evidence"]["unverified_note_ids"]


def test_frontend_fixture_kontrakt_bilan_mos():
    """Frontend testlari `web/src/__tests__/fixtures.json` ga tayanadi.

    Bu yerda javob KALITLARI solishtiriladi (qiymatlar emas — ular
    matn o'zgarganda beso'z yiqilishi kerak emas). Backend javob shakli
    o'zgarsa, frontend testlari eskirib qolgani shu yerda ma'lum bo'ladi.

    Yangilash:
        uv run python scripts/gen_fixtures.py
    """
    import pathlib

    yol = pathlib.Path(__file__).parents[2] / "web/src/__tests__/fixtures.json"
    if not yol.exists():
        pytest.skip("frontend fixture yo'q")

    saqlangan = json.loads(yol.read_text(encoding="utf-8"))
    qismli = {k: v for k, v in TOZA_BLUZKA.items() if k != "mato_turi"}
    joriy = {
        "resolved": tasnif(mijoz(TOZA_BLUZKA)).json(),
        "insufficient": tasnif(mijoz(qismli)).json(),
        "empty": tasnif(mijoz({}), "salom").json(),
    }

    for nom, kutilgan in joriy.items():
        assert set(saqlangan[nom]) == set(kutilgan), (
            f"'{nom}' javobining kalitlari o'zgargan — fixture'ni yangilang:\n"
            f"  qo'shilgan: {set(kutilgan) - set(saqlangan[nom])}\n"
            f"  yo'qolgan:  {set(saqlangan[nom]) - set(kutilgan)}"
        )
        assert saqlangan[nom]["status"] == kutilgan["status"]


def test_javobda_ontologiya_versiyasi_bor():
    """Qaysi ma'lumot bazasi asosida javob berilgani qayd etilishi kerak."""
    b = tasnif(mijoz(TOZA_BLUZKA)).json()
    assert b["ontology_version"]
