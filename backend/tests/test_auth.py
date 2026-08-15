"""10-bosqich: Sessiya va kirish.

Sessiya tokeni bazada XESHLANGAN holda saqlanadi. Ya'ni:

  - Cookie'da: tasodifiy 32 baytli token
  - Bazada:    o'sha tokenning SHA-256 xeshi

Baza o'g'irlansa, undagi yozuvlar bilan hech kimning nomidan kirib
bo'lmaydi — xeshdan tokenni tiklab bo'lmaydi. Bu parol xeshlashning
o'sha mantiqi, sessiyalarga qo'llangan holda.

Ikkinchi muhim xususiyat: kirish xatolari HECH QANDAY ma'lumot
oshkor qilmaydi. "Bunday email yo'q" va "parol noto'g'ri" bir xil
javob beradi — aks holda hujumchi qaysi emaillar ro'yxatdan
o'tganini aniqlay oladi.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.auth import (
    SESSIYA_COOKIE,
    bekor_qil_sessiya,
    sessiya_yarat,
    sessiyadan_foydalanuvchi,
)
from app.models import User, UserSession
from app.security import hash_password

pytestmark = pytest.mark.db

PAROL = "Bluzka-6106-trikotaj"


@pytest.fixture
def user(db) -> User:
    u = User(email="tadbirkor@example.uz", password_hash=hash_password(PAROL))
    db.add(u)
    db.flush()
    return u


# --- Sessiya yaratish -------------------------------------------------------


def test_sessiya_token_qaytaradi(db, user):
    token = sessiya_yarat(db, user)
    assert isinstance(token, str)
    assert len(token) >= 32


def test_har_safar_boshqa_token(db, user):
    assert sessiya_yarat(db, user) != sessiya_yarat(db, user)


def test_bazada_TOKEN_EMAS_XESH_saqlanadi(db, user):
    """⭐⭐ Eng muhim test.

    Bazadagi hech bir ustunda tokenning o'zi bo'lmasligi kerak.
    """
    token = sessiya_yarat(db, user)
    db.flush()
    s = db.execute(select(UserSession)).scalar_one()

    assert s.token_hash != token
    assert s.token_hash == hashlib.sha256(token.encode()).hexdigest()

    # Butun yozuv bo'ylab qidiramiz — token hech qayerda ko'rinmasligi kerak.
    for ustun in s.__table__.columns.keys():
        qiymat = getattr(s, ustun)
        if isinstance(qiymat, str):
            assert token not in qiymat, f"token '{ustun}' ustuniga sizib o'tdi"


def test_sessiya_muddati_belgilanadi(db, user):
    sessiya_yarat(db, user)
    db.flush()
    s = db.execute(select(UserSession)).scalar_one()
    assert s.expires_at > datetime.now(UTC)


def test_kontekst_yoziladi(db, user):
    sessiya_yarat(db, user, user_agent="Mozilla/5.0", ip="203.0.113.7")
    db.flush()
    s = db.execute(select(UserSession)).scalar_one()
    assert s.user_agent == "Mozilla/5.0"
    assert s.ip == "203.0.113.7"


def test_juda_uzun_user_agent_kesiladi(db, user):
    """Brauzer istalgan uzunlikdagi sarlavha yuborishi mumkin — u
    ustun chegarasidan oshib ketmasligi kerak."""
    sessiya_yarat(db, user, user_agent="A" * 5000)
    db.flush()
    s = db.execute(select(UserSession)).scalar_one()
    assert len(s.user_agent) <= 255


# --- Sessiyani tekshirish ---------------------------------------------------


def test_togri_token_foydalanuvchini_qaytaradi(db, user):
    token = sessiya_yarat(db, user)
    db.flush()
    assert sessiyadan_foydalanuvchi(db, token).id == user.id


def test_notogri_token_none(db, user):
    sessiya_yarat(db, user)
    db.flush()
    assert sessiyadan_foydalanuvchi(db, "boshqa-token") is None


def test_bosh_token_none(db):
    assert sessiyadan_foydalanuvchi(db, "") is None
    assert sessiyadan_foydalanuvchi(db, None) is None


def test_muddati_otgan_sessiya_ishlamaydi(db, user):
    token = sessiya_yarat(db, user)
    db.flush()
    s = db.execute(select(UserSession)).scalar_one()
    s.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.flush()
    assert sessiyadan_foydalanuvchi(db, token) is None


def test_bekor_qilingan_sessiya_ishlamaydi(db, user):
    token = sessiya_yarat(db, user)
    db.flush()
    bekor_qil_sessiya(db, token)
    db.flush()
    assert sessiyadan_foydalanuvchi(db, token) is None


def test_bloklangan_foydalanuvchi_sessiyasi_DARHOL_ishlamaydi(db, user):
    """⭐ Admin bloklaganda mavjud sessiya ham to'xtashi kerak.

    Aks holda bloklangan foydalanuvchi sessiyasi tugagunicha
    (2 hafta) ishlashda davom etadi.
    """
    token = sessiya_yarat(db, user)
    db.flush()
    user.is_active = False
    db.flush()
    assert sessiyadan_foydalanuvchi(db, token) is None


def test_bekor_qilish_faqat_ozini_tegadi(db, user):
    birinchi = sessiya_yarat(db, user)
    ikkinchi = sessiya_yarat(db, user)
    db.flush()
    bekor_qil_sessiya(db, birinchi)
    db.flush()
    assert sessiyadan_foydalanuvchi(db, birinchi) is None
    assert sessiyadan_foydalanuvchi(db, ikkinchi) is not None


def test_mavjud_bolmagan_tokenni_bekor_qilish_xato_bermaydi(db):
    bekor_qil_sessiya(db, "yo'q-token")  # jimgina o'tishi kerak


# --- Cookie nomi ------------------------------------------------------------


def test_cookie_nomi_belgilangan():
    assert SESSIYA_COOKIE == "tilmon_session"
