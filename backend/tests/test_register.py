"""11-bosqich: Ro'yxatdan o'tish va taklif kodlari.

Yopiq beta: taklif kodisiz ro'yxatdan o'tib bo'lmaydi. Sabab loyihaga xos —
ma'lumot bazasi hali tasdiqlanmagan, shuning uchun birinchi foydalanuvchilar
doirasi nazorat ostida bo'lishi kerak.

Kod BIR MARTA ishlatiladi. Bu jiddiy talab: aks holda bitta kod tarqalib
ketsa, yopiq beta ochiq bo'lib qoladi.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import app
from app.auth import SESSIYA_COOKIE
from app.db import get_db
from app.invites import kod_yarat
from app.models import InviteCode, User
from app.security import hash_password
from app.throttle import tozala_urinishlar

pytestmark = pytest.mark.db

PAROL = "Bluzka-6106-trikotaj"


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    tozala_urinishlar()
    yield TestClient(app)
    app.dependency_overrides.clear()
    tozala_urinishlar()


@pytest.fixture
def kod(db) -> InviteCode:
    k = InviteCode(code=kod_yarat())
    db.add(k)
    db.flush()
    return k


def royxat(c, kod, email="yangi@example.uz", parol=PAROL):
    return c.post(
        "/api/auth/register",
        json={"email": email, "password": parol, "invite_code": kod},
    )


# --- Kod generatori ---------------------------------------------------------


def test_kod_yetarli_uzun():
    assert len(kod_yarat()) >= 12


def test_kodlar_takrorlanmaydi():
    kodlar = {kod_yarat() for _ in range(500)}
    assert len(kodlar) == 500


def test_kodning_TASODIFIY_qismida_chalkash_belgilar_yoq():
    """0/O va 1/I/l ni telefonda aytib berish qiyin — ular ishlatilmaydi.

    Tekshiruv faqat tasodifiy qismga tegishli: "TILMON" prefiksi ma'lum
    so'z, uni aytib berishda chalkashlik yo'q.
    """
    tasodifiy = "".join(kod_yarat().split("-", 1)[1] for _ in range(200))
    for belgi in "01OIl":
        assert belgi not in tasodifiy, f"'{belgi}' chalkash belgisi ishlatilgan"


def test_kod_tanib_olinadigan_prefiksga_ega():
    assert kod_yarat().startswith("TILMON-")


# --- Muvaffaqiyatli ro'yxat -------------------------------------------------


def test_togri_kod_bilan_royxatdan_otish(client, kod, db):
    r = royxat(client, kod.code)
    assert r.status_code == 201
    assert r.json()["email"] == "yangi@example.uz"
    assert r.json()["role"] == "user"


def test_royxatdan_keyin_darhol_kirgan_holatda(client, kod):
    """Foydalanuvchi ro'yxatdan o'tib, yana alohida kirishi shart emas."""
    r = royxat(client, kod.code)
    assert SESSIYA_COOKIE in r.cookies
    assert client.get("/api/auth/me").status_code == 200


def test_foydalanuvchi_bazada_yaratiladi(client, kod, db):
    royxat(client, kod.code)
    u = db.execute(
        select(User).where(User.email == "yangi@example.uz")
    ).scalar_one()
    assert u.role == "user"
    assert u.is_active is True


def test_parol_xeshlangan_holda_saqlanadi(client, kod, db):
    royxat(client, kod.code)
    u = db.execute(select(User).where(User.email == "yangi@example.uz")).scalar_one()
    assert PAROL not in u.password_hash
    assert u.password_hash.startswith("$argon2id$")


def test_javobda_parol_yoq(client, kod):
    assert PAROL not in royxat(client, kod.code).text


def test_email_kichik_harfga_keltiriladi(client, kod, db):
    royxat(client, kod.code, email="Yangi@Example.UZ")
    assert db.execute(select(User)).scalar_one().email == "yangi@example.uz"


# --- ⭐ Kod bir marta ishlatiladi -------------------------------------------


def test_kod_ishlatilgan_deb_belgilanadi(client, kod, db):
    royxat(client, kod.code)
    db.refresh(kod)
    assert kod.used_at is not None
    assert kod.used_by_id is not None


def test_ishlatilgan_kod_QAYTA_ishlamaydi(client, kod):
    """⭐⭐ Aks holda bitta kod tarqalsa, yopiq beta ochiq bo'lib qoladi."""
    assert royxat(client, kod.code).status_code == 201
    r = royxat(client, kod.code, email="ikkinchi@example.uz")
    assert r.status_code == 400


def test_kod_kim_ishlatganini_yozadi(client, kod, db):
    royxat(client, kod.code)
    db.refresh(kod)
    assert kod.used_by.email == "yangi@example.uz"


# --- Rad etish holatlari ----------------------------------------------------


def test_kodsiz_royxatdan_otib_bolmaydi(client):
    r = client.post(
        "/api/auth/register", json={"email": "a@b.uz", "password": PAROL}
    )
    assert r.status_code == 422


def test_bosh_kod_rad_etiladi(client):
    assert royxat(client, "").status_code == 422


def test_notanish_kod_rad_etiladi(client):
    assert royxat(client, "TILMON-YOQ-KOD").status_code == 400


def test_muddati_otgan_kod_rad_etiladi(client, db):
    k = InviteCode(
        code=kod_yarat(), expires_at=datetime.now(UTC) - timedelta(days=1)
    )
    db.add(k)
    db.flush()
    assert royxat(client, k.code).status_code == 400


def test_muddatsiz_kod_ishlaydi(client, db):
    k = InviteCode(code=kod_yarat(), expires_at=None)
    db.add(k)
    db.flush()
    assert royxat(client, k.code).status_code == 201


def test_takrorlanuvchi_email_409(client, db, kod):
    db.add(User(email="bor@example.uz", password_hash=hash_password(PAROL)))
    db.flush()
    r = royxat(client, kod.code, email="bor@example.uz")
    assert r.status_code == 409


def test_takrorlanuvchi_email_kodni_SARFLAMAYDI(client, db, kod):
    """⭐ Xato so'rov taklif kodini yo'q qilmasligi kerak."""
    db.add(User(email="bor@example.uz", password_hash=hash_password(PAROL)))
    db.flush()
    royxat(client, kod.code, email="bor@example.uz")
    db.refresh(kod)
    assert kod.used_at is None


def test_notogri_kod_holatida_foydalanuvchi_yaratilmaydi(client, db):
    royxat(client, "TILMON-YOQ-KOD")
    assert db.execute(select(User)).first() is None


# --- Parol siyosati ---------------------------------------------------------


@pytest.mark.parametrize(
    "zaif", ["qisqa", "1234567890123", "parol12345", "password123"]
)
def test_zaif_parol_rad_etiladi(client, kod, zaif):
    r = royxat(client, kod.code, parol=zaif)
    assert r.status_code == 422


def test_zaif_parol_xatosi_ozbekcha_va_tushunarli(client, kod):
    r = royxat(client, kod.code, parol="qisqa")
    assert "belgi" in r.text.lower()


def test_zaif_parol_kodni_sarflamaydi(client, kod, db):
    royxat(client, kod.code, parol="qisqa")
    db.refresh(kod)
    assert kod.used_at is None


def test_emailga_oxshash_parol_rad_etiladi(client, kod):
    r = royxat(client, kod.code, email="tadbirkor@example.uz", parol="tadbirkor-2026")
    assert r.status_code == 422
