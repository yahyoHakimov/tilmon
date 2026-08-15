"""15-bosqich: Ishga tushirishdan oldingi tekshiruv.

Ishlab chiqarishdagi eng ko'p uchraydigan xato — sozlamani unutish.
`SECURE_COOKIES=0` qolib ketsa, sessiya ochiq kanalda ketadi va
tarmoqni tinglagan har kim uni o'qiy oladi. `ALLOWED_ORIGINS` da
`localhost` qolsa, CORS ma'nosini yo'qotadi.

Bunday xatolar jimgina o'tadi: ilova ishlaydi, hech narsa yiqilmaydi,
lekin himoya yo'q. Shuning uchun tizim `ENV=production` da xavfsiz
bo'lmagan sozlama bilan ISHGA TUSHMAYDI — ochiq xato bilan to'xtaydi.

Sekin nosozlik jim nosozlikdan yaxshiroq.
"""

from __future__ import annotations

import pytest

from app.config import Settings
from app.preflight import SozlamaXavfli, tekshir

# `openssl rand -hex 32` chiqargan qiymatga o'xshash — bir xil belgidan
# iborat qator ("a"*64) tekshiruvdan o'tmaydi va o'tmasligi ham kerak.
HAQIQIY_SIR = "7f3a9c1e4b8d2065af51c93e7d0b6248195ecf3a4d7b0c826f19e35a8db4c70f"

XAVFSIZ = dict(
    DATABASE_URL="postgresql+psycopg://tilmon:kuchli-parol@127.0.0.1:5432/tilmon",
    SESSION_SECRET=HAQIQIY_SIR,
    SECURE_COOKIES="1",
    ALLOWED_ORIGINS="https://tilmon.uz",
    OPENAI_API_KEY="sk-test-kalit",
)


def sozlama(**almashtirish) -> Settings:
    return Settings(**{**XAVFSIZ, **almashtirish})


def test_xavfsiz_sozlama_otadi():
    tekshir(sozlama())  # xato ko'tarmasligi kerak


# --- ⭐ Cookie xavfsizligi --------------------------------------------------


def test_secure_cookies_ochiq_bolsa_TOXTAYDI():
    """⭐⭐ Eng muhim tekshiruv.

    Bu bayroqsiz sessiya cookie'si HTTP orqali ham yuboriladi.
    Ochiq Wi-Fi da o'tirgan har kim uni o'qiy oladi va foydalanuvchi
    nomidan kira oladi.
    """
    with pytest.raises(SozlamaXavfli, match="SECURE_COOKIES"):
        tekshir(sozlama(SECURE_COOKIES="0"))


# --- Sirlar -----------------------------------------------------------------


def test_sessiya_siri_bosh_bolsa_toxtaydi():
    with pytest.raises(SozlamaXavfli, match="SESSION_SECRET"):
        tekshir(sozlama(SESSION_SECRET=""))


def test_qisqa_sessiya_siri_qabul_qilinmaydi():
    with pytest.raises(ValueError):
        sozlama(SESSION_SECRET="qisqa")


def test_namunaviy_sir_qabul_qilinmaydi():
    """`.env.example` dan ko'chirilgan qiymat ishlab chiqarishga o'tmasligi kerak."""
    for namuna in ("o'zgartiring", "changeme", "secret"):
        # Uzunlik yetarli, lekin ichida namunaviy so'z bor.
        with pytest.raises(SozlamaXavfli, match="SESSION_SECRET"):
            tekshir(sozlama(SESSION_SECRET=namuna + HAQIQIY_SIR[: 40]))


# --- Ma'lumotlar bazasi -----------------------------------------------------


def test_ishlab_chiqishdagi_parol_qabul_qilinmaydi():
    """`tilmon_dev` — `.env.example` dagi parol, u serverga tushmasligi kerak."""
    with pytest.raises(SozlamaXavfli, match="parol"):
        tekshir(
            sozlama(
                DATABASE_URL="postgresql+psycopg://tilmon:tilmon_dev@127.0.0.1:5432/tilmon"
            )
        )


def test_parolsiz_baza_qabul_qilinmaydi():
    with pytest.raises(SozlamaXavfli, match="parol"):
        tekshir(sozlama(DATABASE_URL="postgresql+psycopg://tilmon@127.0.0.1:5432/tilmon"))


def test_sqlite_qabul_qilinmaydi():
    with pytest.raises(SozlamaXavfli, match="Postgres"):
        tekshir(sozlama(DATABASE_URL="sqlite:///tilmon.db"))


# --- CORS -------------------------------------------------------------------


def test_localhost_origin_qabul_qilinmaydi():
    with pytest.raises(SozlamaXavfli, match="ALLOWED_ORIGINS"):
        tekshir(sozlama(ALLOWED_ORIGINS="http://localhost:5173"))


def test_http_origin_qabul_qilinmaydi():
    """HTTPS bo'lmasa `Secure` cookie yetib bormaydi — kirish ishlamaydi."""
    with pytest.raises(SozlamaXavfli, match="https"):
        tekshir(sozlama(ALLOWED_ORIGINS="http://tilmon.uz"))


def test_yulduzcha_origin_qabul_qilinmaydi():
    with pytest.raises(SozlamaXavfli, match="ALLOWED_ORIGINS"):
        tekshir(sozlama(ALLOWED_ORIGINS="*"))


def test_bosh_origin_qabul_qilinmaydi():
    with pytest.raises(SozlamaXavfli, match="ALLOWED_ORIGINS"):
        tekshir(sozlama(ALLOWED_ORIGINS=""))


# --- Ogohlantirishlar (to'xtatmaydi) ---------------------------------------


def test_openai_kaliti_yoq_bolsa_ogohlantiradi_lekin_toxtatmaydi():
    """Kalitsiz tizim ishlaydi — faqat erkin matn tahlil qilinmaydi.

    Bu xavfsizlik muammosi emas, funksionallik cheklovi.
    """
    ogohlantirishlar = tekshir(sozlama(OPENAI_API_KEY=""))
    assert any("OPENAI_API_KEY" in o for o in ogohlantirishlar)


def test_xavfsiz_sozlamada_ogohlantirish_yoq():
    assert tekshir(sozlama()) == []


# --- Barcha muammolar birdaniga ko'rsatiladi -------------------------------


def test_bir_nechta_muammo_BIR_XATODA_korsatiladi():
    """⭐ Har safar bittadan tuzatib, qayta ishga tushirish — vaqt yo'qotish.

    Barcha muammolar bir marta ro'yxat qilib beriladi.
    """
    with pytest.raises(SozlamaXavfli) as e:
        tekshir(
            sozlama(SECURE_COOKIES="0", SESSION_SECRET="", ALLOWED_ORIGINS="*")
        )
    matn = str(e.value)
    assert "SECURE_COOKIES" in matn
    assert "SESSION_SECRET" in matn
    assert "ALLOWED_ORIGINS" in matn


def test_xato_matni_nima_qilishni_aytadi():
    """Xato "noto'g'ri" demasligi, "shunday qiling" deyishi kerak."""
    with pytest.raises(SozlamaXavfli) as e:
        tekshir(sozlama(SESSION_SECRET=""))
    assert "openssl rand" in str(e.value)
