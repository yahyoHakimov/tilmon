"""10-bosqich (2-qism): Kirish endpointlari.

Ikkita xavfsizlik talabi bu yerda test bilan mustahkamlanadi:

1. **Kirish xatolari ma'lumot oshkor qilmaydi.** "Bunday email yo'q" va
   "parol noto'g'ri" bir xil javob beradi. Aks holda hujumchi shu farq
   orqali qaysi emaillar ro'yxatdan o'tganini aniqlay oladi.

2. **Cookie JavaScript uchun ko'rinmas.** `HttpOnly` bayrog'i XSS
   hujumida sessiya o'g'irlanishining oldini oladi.

Uchinchisi — brute-force cheklovi: bir nechta muvaffaqiyatsiz
urinishdan keyin 429.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import app
from app.auth import SESSIYA_COOKIE
from app.db import get_db
from app.models import User, UserSession
from app.security import SOXTA_XESH, hash_password
from app.throttle import tozala_urinishlar

pytestmark = pytest.mark.db

PAROL = "Bluzka-6106-trikotaj"
EMAIL = "tadbirkor@example.uz"


@pytest.fixture
def user(db) -> User:
    u = User(email=EMAIL, password_hash=hash_password(PAROL))
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def client(db):
    """TestClient test tranzaksiyasidagi sessiyani ishlatadi.

    Shunda endpoint yaratgan yozuvlar test oxirida bekor qilinadi.
    """
    app.dependency_overrides[get_db] = lambda: db
    tozala_urinishlar()
    yield TestClient(app)
    app.dependency_overrides.clear()
    tozala_urinishlar()


def kir(c, email=EMAIL, parol=PAROL):
    return c.post("/api/auth/login", json={"email": email, "password": parol})


# --- Muvaffaqiyatli kirish --------------------------------------------------


def test_togri_malumot_bilan_kirish(client, user):
    r = kir(client)
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL
    assert r.json()["role"] == "user"


def test_kirish_cookie_ornatadi(client, user):
    r = kir(client)
    assert SESSIYA_COOKIE in r.cookies


def test_cookie_httponly_va_samesite(client, user):
    """⭐ HttpOnly — XSS hujumida sessiya o'g'irlanmasligi uchun."""
    r = kir(client)
    sarlavha = r.headers["set-cookie"].lower()
    assert "httponly" in sarlavha
    assert "samesite=lax" in sarlavha
    assert "path=/" in sarlavha


def test_secure_cookie_sozlamasi_varsayilgan_holda_YOQILGAN():
    """⭐ Ishlab chiqarishda cookie faqat HTTPS orqali yuborilishi kerak.

    Testlar HTTP da ishlagani uchun `SECURE_COOKIES=0` qilinadi
    (conftest.py). Lekin VARSAYILGAN qiymat `True` bo'lishi shart —
    kimdir uni o'zgartirsa, ishlab chiqarishda sessiya ochiq kanalda
    ketadi va tarmoqni tinglagan har kim uni o'qiy oladi.
    """
    from app.config import Settings

    assert Settings.model_fields["secure_cookies"].default is True


def test_javobda_parol_xeshi_YOQ(client, user):
    """⭐ Foydalanuvchi obyekti hech qachon to'liq serializatsiya
    qilinmasligi kerak."""
    matn = kir(client).text
    assert "password" not in matn.lower()
    assert "argon2" not in matn


def test_kirish_last_login_ni_yangilaydi(client, user, db):
    assert user.last_login_at is None
    kir(client)
    db.refresh(user)
    assert user.last_login_at is not None
    assert (datetime.now(UTC) - user.last_login_at).total_seconds() < 10


def test_email_registri_muhim_emas(client, user):
    assert kir(client, email="TadBirkor@Example.UZ").status_code == 200


def test_email_atrofidagi_probellar_tozalanadi(client, user):
    assert kir(client, email=f"  {EMAIL}  ").status_code == 200


# --- ⭐ Ma'lumot oshkor qilmaslik -------------------------------------------


def test_notogri_parol_401(client, user):
    r = kir(client, parol="boshqa-parol-9999")
    assert r.status_code == 401
    assert SESSIYA_COOKIE not in r.cookies


def test_mavjud_bolmagan_email_401(client, user):
    assert kir(client, email="yoq@example.uz").status_code == 401


def test_ikki_xato_BIR_XIL_javob_beradi(client, user):
    """⭐⭐ Javob matni email mavjudligini oshkor qilmasligi kerak."""
    yoq = kir(client, email="yoq@example.uz")
    tozala_urinishlar()
    notogri = kir(client, parol="boshqa-parol-9999")

    assert yoq.status_code == notogri.status_code == 401
    assert yoq.json() == notogri.json()


def test_mavjud_bolmagan_email_uchun_ham_PAROL_TEKSHIRILADI(client, monkeypatch):
    """⭐⭐ Vaqt hujumiga qarshi himoya.

    Foydalanuvchi topilmasa darhol 401 qaytarsak, javob mavjud
    foydalanuvchinikidan sezilarli tez keladi (argon2 ataylab sekin).
    Hujumchi shu farqni o'lchab, qaysi emaillar ro'yxatdan o'tganini
    aniqlay oladi.

    Vaqtni o'lchash o'rniga XATTI-HARAKATNI tekshiramiz: topilmagan
    holatda ham `verify_password` soxta xesh bilan chaqirilishi shart.
    Vaqt o'lchaydigan test CI da beqaror bo'lardi.
    """
    from app import api_auth

    chaqirilgan_xeshlar = []
    asl = api_auth.verify_password

    def kuzatuvchi(xesh, parol):
        chaqirilgan_xeshlar.append(xesh)
        return asl(xesh, parol)

    monkeypatch.setattr(api_auth, "verify_password", kuzatuvchi)
    kir(client, email="mutlaqo-yoq@example.uz")

    assert chaqirilgan_xeshlar == [SOXTA_XESH], (
        "topilmagan foydalanuvchi uchun parol tekshiruvi o'tkazib "
        "yuborildi — javob vaqti email mavjudligini oshkor qiladi"
    )


def test_bloklangan_foydalanuvchi_kira_olmaydi(client, user, db):
    user.is_active = False
    db.flush()
    assert kir(client).status_code == 401


def test_bloklangan_foydalanuvchi_javobi_ham_bir_xil(client, user, db):
    """Blok holati ham oshkor qilinmaydi."""
    user.is_active = False
    db.flush()
    bloklangan = kir(client)
    tozala_urinishlar()
    yoq = kir(client, email="yoq@example.uz")
    assert bloklangan.json() == yoq.json()


# --- Kiritmani tekshirish ---------------------------------------------------


@pytest.mark.parametrize(
    "tana",
    [
        {},
        {"email": EMAIL},
        {"password": PAROL},
        {"email": "", "password": PAROL},
        {"email": "email emas", "password": PAROL},
        {"email": EMAIL, "password": ""},
    ],
)
def test_notogri_kiritma_422(client, tana):
    assert client.post("/api/auth/login", json=tana).status_code == 422


# --- /me --------------------------------------------------------------------


def test_me_cookiesiz_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_kirgandan_keyin_ishlaydi(client, user):
    kir(client)
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == EMAIL


def test_me_javobida_faqat_kerakli_maydonlar(client, user):
    kir(client)
    b = client.get("/api/auth/me").json()
    assert set(b) == {"id", "email", "role", "created_at"}


def test_soxta_cookie_bilan_401(client, user):
    client.cookies.set(SESSIYA_COOKIE, "soxta-token-12345")
    assert client.get("/api/auth/me").status_code == 401


# --- Chiqish ----------------------------------------------------------------


def test_chiqish_sessiyani_bekor_qiladi(client, user, db):
    kir(client)
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401

    s = db.execute(select(UserSession)).scalar_one()
    assert s.revoked_at is not None


def test_chiqish_cookieni_ochiradi(client, user):
    kir(client)
    r = client.post("/api/auth/logout")
    assert 'tilmon_session=""' in r.headers.get("set-cookie", "") or (
        "tilmon_session=;" in r.headers.get("set-cookie", "")
    )


def test_kirmasdan_chiqish_xato_bermaydi(client):
    assert client.post("/api/auth/logout").status_code == 204


# --- ⭐ Brute-force cheklovi ------------------------------------------------


def test_kop_muvaffaqiyatsiz_urinishdan_keyin_429(client, user):
    """Parolni taxmin qilishga urinish cheklanadi."""
    for _ in range(10):
        kir(client, parol="notogri-parol-123")
    r = kir(client, parol="notogri-parol-123")
    assert r.status_code == 429


def test_cheklovdan_keyin_TOGRI_parol_ham_ishlamaydi(client, user):
    """⭐ Aks holda cheklov taxmin qilishni to'xtatmaydi — hujumchi
    to'g'ri parolni topganini baribir bilib oladi."""
    for _ in range(10):
        kir(client, parol="notogri-parol-123")
    assert kir(client).status_code == 429


def test_muvaffaqiyatli_kirish_hisobni_tozalaydi(client, user):
    for _ in range(3):
        kir(client, parol="notogri-parol-123")
    assert kir(client).status_code == 200
    for _ in range(3):
        kir(client, parol="notogri-parol-123")
    assert kir(client).status_code == 200


def test_cheklov_email_boyicha_ajratilgan(client, user, db):
    """Bir foydalanuvchini bloklash boshqasini to'sib qo'ymasligi kerak."""
    ikkinchi = User(email="ikkinchi@example.uz", password_hash=hash_password(PAROL))
    db.add(ikkinchi)
    db.flush()

    for _ in range(10):
        kir(client, parol="notogri-parol-123")
    assert kir(client).status_code == 429
    assert kir(client, email="ikkinchi@example.uz").status_code == 200
