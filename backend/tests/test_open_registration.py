"""Ochiq ro'yxatdan o'tish rejimi.

Yopiq beta — dastlabki holat. Demo va sinov davrida uni ochish kerak
bo'ladi, lekin bu QAYTARILADIGAN qaror bo'lishi shart: `.env` dagi
bitta bayroq, kod o'zgarishi emas.

Ikkita muhim qoida:

1. **Sukut bo'yicha YOPIQ.** Ochish uchun kimdir uni ataylab yoqishi
   kerak. Aks holda yangi muhitda (yangi server, yangi ishlab chiquvchi)
   ro'yxat tasodifan ochiq qolishi mumkin.

2. **Ochiq rejimda ham noto'g'ri kod rad etiladi.** Agar foydalanuvchi
   kod kiritsa, u haqiqiy bo'lishi kerak — aks holda "kodim ishladi"
   deb o'ylab qoladi, aslida esa kod umuman o'qilmagan bo'lardi.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.auth import SESSIYA_COOKIE
from app.config import Settings, get_settings
from app.db import get_db
from app.invites import kod_yarat
from app.models import InviteCode, User
from app.throttle import tozala_urinishlar

pytestmark = pytest.mark.db

PAROL = "Bluzka-6106-trikotaj"


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    tozala_urinishlar()
    yield TestClient(app)
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    tozala_urinishlar()


@pytest.fixture
def ochiq(monkeypatch):
    """Ro'yxatni ochadi."""
    monkeypatch.setenv("REGISTRATION_OPEN", "1")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def kod(db) -> InviteCode:
    k = InviteCode(code=kod_yarat())
    db.add(k)
    db.flush()
    return k


def royxat(c, **maydonlar):
    tana = {"email": "yangi@example.uz", "password": PAROL, **maydonlar}
    return c.post("/api/auth/register", json=tana)


# --- ⭐ Sukut bo'yicha yopiq ------------------------------------------------


def test_varsayilgan_qiymat_YOPIQ():
    """⭐⭐ Yangi muhitda ro'yxat tasodifan ochiq qolmasligi kerak."""
    assert Settings.model_fields["registration_open"].default is False


def test_yopiq_rejimda_kodsiz_royxat_yoq(client):
    assert royxat(client).status_code == 422


def test_yopiq_rejimda_kod_bilan_ishlaydi(client, kod):
    assert royxat(client, invite_code=kod.code).status_code == 201


# --- Ochiq rejim ------------------------------------------------------------


def test_ochiq_rejimda_kodsiz_royxatdan_otish(client, ochiq):
    r = royxat(client)
    assert r.status_code == 201
    assert r.json()["email"] == "yangi@example.uz"


def test_ochiq_rejimda_ham_darhol_kirgan_holatda(client, ochiq):
    r = royxat(client)
    assert SESSIYA_COOKIE in r.cookies
    assert client.get("/api/auth/me").status_code == 200


def test_ochiq_rejimda_rol_user(client, ochiq, db):
    royxat(client)
    from sqlalchemy import select

    u = db.execute(select(User).where(User.email == "yangi@example.uz")).scalar_one()
    assert u.role == "user"


def test_ochiq_rejimda_bosh_kod_qabul_qilinadi(client, ochiq):
    """Frontend bo'sh maydon yuborishi mumkin."""
    assert royxat(client, invite_code="").status_code == 201


def test_ochiq_rejimda_haqiqiy_kod_ishlaydi_va_sarflanadi(client, ochiq, kod, db):
    assert royxat(client, invite_code=kod.code).status_code == 201
    db.refresh(kod)
    assert kod.used_at is not None


def test_ochiq_rejimda_ham_NOTOGRI_kod_rad_etiladi(client, ochiq):
    """⭐ Kod kiritilgan bo'lsa, u haqiqiy bo'lishi kerak.

    Aks holda foydalanuvchi "kodim ishladi" deb o'ylaydi, aslida esa
    kod umuman o'qilmagan bo'lardi.
    """
    assert royxat(client, invite_code="TILMON-YOQ-KOD").status_code == 400


def test_ochiq_rejimda_ham_parol_siyosati_amal_qiladi(client, ochiq):
    assert royxat(client, password="qisqa").status_code == 422


def test_ochiq_rejimda_ham_takrorlanuvchi_email_409(client, ochiq):
    assert royxat(client).status_code == 201
    assert royxat(client).status_code == 409


# --- Ochiq endpoint: frontend holatni bilishi kerak ------------------------


def test_config_endpointi_ochiq(client):
    r = client.get("/api/auth/config")
    assert r.status_code == 200
    assert r.json()["registration_open"] is False


def test_config_ochiq_rejimni_koradi(client, ochiq):
    assert client.get("/api/auth/config").json()["registration_open"] is True


def test_config_hech_qanday_sir_bermaydi(client):
    """Endpoint kirishsiz ochiq — unda faqat shu bitta bayroq bo'lishi kerak."""
    assert set(client.get("/api/auth/config").json()) == {"registration_open"}
