"""9-bosqich (2-qism): Ma'lumotlar bazasi modellari.

Uchta jadval: foydalanuvchilar, sessiyalar, taklif kodlari.

Eng muhim xavfsizlik xususiyati sessiya jadvalida: bazada sessiya
tokenining O'ZI emas, uning xeshi saqlanadi. Baza o'g'irlansa, undagi
yozuvlar bilan hech kimning nomidan kirib bo'lmaydi.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import ROLLAR, InviteCode, User, UserSession
from app.security import hash_password

pytestmark = pytest.mark.db


def foydalanuvchi(**qoshimcha) -> User:
    asos = dict(
        email="tadbirkor@example.uz",
        password_hash=hash_password("Bluzka-6106-trikotaj"),
    )
    return User(**{**asos, **qoshimcha})


# --- Foydalanuvchi ----------------------------------------------------------


def test_foydalanuvchi_saqlanadi(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    assert u.id is not None
    assert u.created_at is not None


def test_email_kichik_harfga_keltiriladi(db):
    u = foydalanuvchi(email="  Tadbirkor@Example.UZ  ")
    db.add(u)
    db.flush()
    assert u.email == "tadbirkor@example.uz"


def test_email_unikal(db):
    db.add(foydalanuvchi())
    db.flush()
    db.add(foydalanuvchi())
    with pytest.raises(IntegrityError):
        db.flush()


def test_email_unikalligi_registrga_sezgir_emas(db):
    """⭐ "Ali@mail.uz" va "ali@mail.uz" — bitta odam."""
    db.add(foydalanuvchi(email="Ali@Mail.uz"))
    db.flush()
    db.add(foydalanuvchi(email="ali@mail.uz"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_varsayilgan_rol_user(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    assert u.role == "user"


def test_varsayilgan_holat_faol(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    assert u.is_active is True


def test_notogri_rol_qabul_qilinmaydi(db):
    """Baza darajasidagi cheklov — kod xato qilsa ham 'superadmin' kirmaydi."""
    db.add(foydalanuvchi(role="superadmin"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_rollar_royxati_kutilganday():
    assert ROLLAR == ("user", "admin")


def test_parol_xeshi_ustuni_bor_lekin_parol_ustuni_yoq():
    """Model'da hech qachon ochiq parol maydoni bo'lmasligi kerak."""
    ustunlar = {c.key for c in inspect(User).columns}
    assert "password_hash" in ustunlar
    assert "password" not in ustunlar
    assert "parol" not in ustunlar


# --- Sessiya ----------------------------------------------------------------


def sessiya(u: User, **qoshimcha) -> UserSession:
    asos = dict(
        user_id=u.id,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    return UserSession(**{**asos, **qoshimcha})


def test_sessiya_saqlanadi(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    s = sessiya(u)
    db.add(s)
    db.flush()
    assert s.id is not None


def test_sessiya_jadvalida_ochiq_token_ustuni_YOQ():
    """⭐⭐ Bazada tokenning o'zi saqlanmaydi, faqat xeshi.

    Baza o'g'irlansa, undagi yozuvlar bilan hech kimning nomidan kirib
    bo'lmaydi — xeshdan tokenni tiklab bo'lmaydi.
    """
    ustunlar = {c.key for c in inspect(UserSession).columns}
    assert "token_hash" in ustunlar
    assert "token" not in ustunlar


def test_sessiya_token_xeshi_unikal(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    db.add(sessiya(u))
    db.flush()
    db.add(sessiya(u))
    with pytest.raises(IntegrityError):
        db.flush()


def test_sessiya_foydalanuvchiga_bogliq(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    db.add(sessiya(u))
    db.flush()
    topildi = db.execute(
        select(UserSession).where(UserSession.user_id == u.id)
    ).scalar_one()
    assert topildi.user.email == u.email


def test_foydalanuvchi_ochirilsa_sessiyalari_ham_ochiriladi(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    db.add(sessiya(u))
    db.flush()
    db.delete(u)
    db.flush()
    assert db.execute(select(UserSession)).first() is None


def test_sessiya_bekor_qilinishi_mumkin(db):
    u = foydalanuvchi()
    db.add(u)
    db.flush()
    s = sessiya(u)
    db.add(s)
    db.flush()
    assert s.revoked_at is None
    s.revoked_at = datetime.now(UTC)
    db.flush()
    assert s.revoked_at is not None


# --- Taklif kodi ------------------------------------------------------------


def test_taklif_kodi_saqlanadi(db):
    k = InviteCode(code="TILMON-XYZ123", expires_at=datetime.now(UTC) + timedelta(days=30))
    db.add(k)
    db.flush()
    assert k.id is not None
    assert k.used_at is None
    assert k.used_by_id is None


def test_taklif_kodi_unikal(db):
    for _ in range(2):
        db.add(InviteCode(code="TILMON-BIRXIL"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_taklif_kodi_kim_ishlatganini_yozadi(db):
    u = foydalanuvchi()
    k = InviteCode(code="TILMON-ABC999")
    db.add_all([u, k])
    db.flush()
    k.used_by_id = u.id
    k.used_at = datetime.now(UTC)
    db.flush()
    assert k.used_by.email == u.email


def test_taklif_kodi_kim_yaratganini_yozadi(db):
    """Audit uchun: qaysi admin kimni taklif qilgani ma'lum bo'lishi kerak."""
    admin = foydalanuvchi(email="admin@example.uz", role="admin")
    db.add(admin)
    db.flush()
    k = InviteCode(code="TILMON-QQQ111", created_by_id=admin.id)
    db.add(k)
    db.flush()
    assert k.created_by.role == "admin"
