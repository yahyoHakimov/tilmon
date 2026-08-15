"""12-bosqich: Huquqlar (authz) va himoyalangan API.

Uchta qatlam:

1. **Tasnif endpointi kirish talab qiladi.** Yopiq beta — anonim
   foydalanuvchi tasnif qila olmaydi. Bu OpenAI xarajatini ham
   nazorat qiladi.
2. **Admin endpointlari faqat adminga.** Oddiy foydalanuvchi 403 oladi.
3. **So'rov limiti.** Bir foydalanuvchi soatiga cheklangan miqdorda
   tasnif qiladi.

Ochiq qoladigan endpointlar aniq ro'yxatga olingan va test bilan
qulflangan: kimdir tasodifan `/api/classify` ni ochiq qoldirsa,
test yiqiladi.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import app, get_client
from app.auth import sessiya_yarat
from app.db import get_db
from app.models import InviteCode, User, UserSession
from app.security import hash_password
from app.throttle import tozala_urinishlar

pytestmark = pytest.mark.db

PAROL = "Bluzka-6106-trikotaj"

TOZA = {
    "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred"},
    "mato_turi": {"value": "trikotaj", "source": "stated"},
    "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated"},
    "jins": {"value": "ayol", "source": "stated"},
    "tarkib": {"value": "paxta", "source": "stated"},
}


class FakeLLM:
    def complete(self, system, user):
        return json.dumps({"attributes": TOZA})


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_client] = lambda: FakeLLM()
    tozala_urinishlar()
    yield TestClient(app)
    app.dependency_overrides.clear()
    tozala_urinishlar()


def _user(db, email, role="user") -> User:
    u = User(email=email, password_hash=hash_password(PAROL), role=role)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def oddiy(db):
    return _user(db, "user@example.uz")


@pytest.fixture
def admin(db):
    return _user(db, "admin@example.uz", role="admin")


def kirgan(client, db, u) -> TestClient:
    """Foydalanuvchi nomidan kirgan mijoz qaytaradi."""
    token = sessiya_yarat(db, u)
    db.flush()
    client.cookies.set("tilmon_session", token)
    return client


def tasnif(c):
    return c.post("/api/classify", json={"text": "ayollar bluzkasi, paxta, trikotaj"})


# --- ⭐ Tasnif endpointi himoyalangan ---------------------------------------


def test_anonim_tasnif_qila_olmaydi(client):
    """⭐⭐ Yopiq beta: kirmasdan tasnif yo'q."""
    assert tasnif(client).status_code == 401


def test_kirgan_foydalanuvchi_tasnif_qiladi(client, db, oddiy):
    r = tasnif(kirgan(client, db, oddiy))
    assert r.status_code == 200
    assert r.json()["code"] == "6106 10 000 0"


def test_soxta_cookie_bilan_tasnif_yoq(client):
    client.cookies.set("tilmon_session", "soxta")
    assert tasnif(client).status_code == 401


def test_bloklangan_foydalanuvchi_tasnif_qila_olmaydi(client, db, oddiy):
    c = kirgan(client, db, oddiy)
    assert tasnif(c).status_code == 200
    oddiy.is_active = False
    db.flush()
    assert tasnif(c).status_code == 401


# --- Ochiq endpointlar ------------------------------------------------------


@pytest.mark.parametrize("yol", ["/api/healthz", "/api/attributes"])
def test_ochiq_endpointlar_kirishsiz_ishlaydi(client, yol):
    assert client.get(yol).status_code == 200


def test_OCHIQ_ENDPOINTLAR_ROYXATI_qulflangan(client):
    """⭐ Kimdir tasodifan yangi endpointni ochiq qoldirmasligi uchun.

    Har bir GET/POST yo'l kirishsiz sinaladi. Ro'yxatda bo'lmagan
    endpoint 401 yoki 403 qaytarishi shart.
    """
    OCHIQ = {
        ("GET", "/api/healthz"),
        ("GET", "/api/attributes"),
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/register"),
        ("POST", "/api/auth/logout"),
    }

    ruxsatsiz = []
    for route in app.routes:
        yollar = getattr(route, "path", None)
        usullar = getattr(route, "methods", None) or set()
        if not yollar or not yollar.startswith("/api/"):
            continue
        for usul in usullar & {"GET", "POST", "PATCH", "DELETE"}:
            if (usul, yollar) in OCHIQ:
                continue
            # Yo'l parametrlarini to'ldiramiz.
            haqiqiy = yollar.replace(
                "{user_id}", "00000000-0000-0000-0000-000000000000"
            )
            r = client.request(usul, haqiqiy, json={})
            if r.status_code not in (401, 403):
                ruxsatsiz.append(f"{usul} {yollar} -> {r.status_code}")

    assert not ruxsatsiz, f"himoyalanmagan endpointlar: {ruxsatsiz}"


# --- ⭐ Admin endpointlari --------------------------------------------------


ADMIN_YOLLARI = [
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/invites"),
]


@pytest.mark.parametrize("usul,yol", ADMIN_YOLLARI)
def test_anonim_admin_endpointiga_401(client, usul, yol):
    assert client.request(usul, yol, json={}).status_code == 401


@pytest.mark.parametrize("usul,yol", ADMIN_YOLLARI)
def test_oddiy_foydalanuvchi_admin_endpointiga_403(client, db, oddiy, usul, yol):
    """⭐⭐ Rol tekshiruvi — kirgan bo'lish yetarli emas."""
    c = kirgan(client, db, oddiy)
    assert c.request(usul, yol, json={}).status_code == 403


@pytest.mark.parametrize("usul,yol", ADMIN_YOLLARI)
def test_admin_kira_oladi(client, db, admin, usul, yol):
    c = kirgan(client, db, admin)
    assert c.request(usul, yol, json={}).status_code in (200, 201)


def test_admin_foydalanuvchilar_royxatini_koradi(client, db, admin, oddiy):
    b = kirgan(client, db, admin).get("/api/admin/users").json()
    emaillar = {u["email"] for u in b["users"]}
    assert {"admin@example.uz", "user@example.uz"} <= emaillar


def test_foydalanuvchilar_royxatida_parol_xeshi_YOQ(client, db, admin, oddiy):
    matn = kirgan(client, db, admin).get("/api/admin/users").text
    assert "argon2" not in matn
    assert "password_hash" not in matn


def test_admin_taklif_kodi_yaratadi(client, db, admin):
    r = kirgan(client, db, admin).post("/api/admin/invites", json={"note": "Aziz aka"})
    assert r.status_code == 201
    kod = r.json()["code"]
    assert kod.startswith("TILMON-")

    k = db.execute(select(InviteCode).where(InviteCode.code == kod)).scalar_one()
    assert k.created_by_id == admin.id
    assert k.note == "Aziz aka"


def test_yaratilgan_kod_darhol_ishlaydi(client, db, admin):
    kod = kirgan(client, db, admin).post("/api/admin/invites", json={}).json()["code"]
    client.cookies.clear()
    r = client.post(
        "/api/auth/register",
        json={"email": "yangi@example.uz", "password": PAROL, "invite_code": kod},
    )
    assert r.status_code == 201


# --- Bloklash ---------------------------------------------------------------


def test_admin_foydalanuvchini_bloklaydi(client, db, admin, oddiy):
    c = kirgan(client, db, admin)
    r = c.post(f"/api/admin/users/{oddiy.id}/block", json={})
    assert r.status_code == 200
    db.refresh(oddiy)
    assert oddiy.is_active is False


def test_bloklash_SESSIYALARNI_ham_bekor_qiladi(client, db, admin, oddiy):
    """⭐ Aks holda bloklangan foydalanuvchi sessiyasi tugagunicha ishlaydi."""
    sessiya_yarat(db, oddiy)
    db.flush()

    kirgan(client, db, admin).post(f"/api/admin/users/{oddiy.id}/block", json={})
    db.flush()

    sessiyalar = db.execute(
        select(UserSession).where(UserSession.user_id == oddiy.id)
    ).scalars().all()
    assert sessiyalar
    assert all(s.revoked_at is not None for s in sessiyalar)


def test_admin_ozini_bloklay_olmaydi(client, db, admin):
    """Oxirgi admin o'zini bloklab, tizimni boshqaruvsiz qoldirmasligi kerak."""
    r = kirgan(client, db, admin).post(f"/api/admin/users/{admin.id}/block", json={})
    assert r.status_code == 400


def test_blokni_yechish(client, db, admin, oddiy):
    c = kirgan(client, db, admin)
    c.post(f"/api/admin/users/{oddiy.id}/block", json={})
    r = c.post(f"/api/admin/users/{oddiy.id}/unblock", json={})
    assert r.status_code == 200
    db.refresh(oddiy)
    assert oddiy.is_active is True


def test_mavjud_bolmagan_foydalanuvchini_bloklash_404(client, db, admin):
    yoq = "00000000-0000-0000-0000-000000000000"
    r = kirgan(client, db, admin).post(f"/api/admin/users/{yoq}/block", json={})
    assert r.status_code == 404


# --- ⭐ So'rov limiti -------------------------------------------------------


def test_sorov_limitidan_oshsa_429(client, db, oddiy, monkeypatch):
    """OpenAI xarajatini nazorat qiladi va suiiste'molni to'xtatadi."""
    from app import api

    monkeypatch.setattr(api, "_limit_soatiga", lambda: 3)
    c = kirgan(client, db, oddiy)
    for _ in range(3):
        assert tasnif(c).status_code == 200
    assert tasnif(c).status_code == 429


def test_limit_foydalanuvchilar_orasida_ajratilgan(client, db, oddiy, monkeypatch):
    from app import api

    monkeypatch.setattr(api, "_limit_soatiga", lambda: 2)
    boshqa = _user(db, "boshqa@example.uz")

    c = kirgan(client, db, oddiy)
    for _ in range(2):
        tasnif(c)
    assert tasnif(c).status_code == 429

    client.cookies.clear()
    assert tasnif(kirgan(client, db, boshqa)).status_code == 200
