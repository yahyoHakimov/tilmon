"""Administrator endpointlari: /api/admin/*

Barcha yo'llar `admin_talab` bog'liqligi orqali o'tadi — router
darajasida, endpoint darajasida emas. Shunda yangi endpoint qo'shilganda
uni himoyalashni unutib bo'lmaydi.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api_auth import admin_talab
from app.auth import bekor_qil_barcha_sessiyalar
from app.db import get_db
from app.invites import kod_yarat
from app.models import InviteCode, User

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    # Himoya router darajasida: yangi endpoint qo'shilganda avtomatik
    # qo'llanadi.
    dependencies=[Depends(admin_talab)],
)

TAKLIF_MUDDATI_KUN = 30


class InviteRequest(BaseModel):
    note: str | None = Field(default=None, max_length=255)
    days: int = Field(default=TAKLIF_MUDDATI_KUN, ge=1, le=365)


@router.get("/users")
def users(db: DbSession = Depends(get_db)) -> dict:
    """Foydalanuvchilar ro'yxati.

    `password_hash` ATAYLAB qaytarilmaydi — model to'g'ridan-to'g'ri
    serializatsiya qilinmaydi, faqat shu lug'at orqali chiqadi.
    """
    royxat = db.execute(select(User).order_by(User.created_at.desc())).scalars()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login_at": (
                    u.last_login_at.isoformat() if u.last_login_at else None
                ),
            }
            for u in royxat
        ]
    }


@router.get("/invites")
def invites(db: DbSession = Depends(get_db)) -> dict:
    royxat = db.execute(
        select(InviteCode).order_by(InviteCode.created_at.desc())
    ).scalars()
    return {
        "invites": [
            {
                "code": k.code,
                "note": k.note,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "used_at": k.used_at.isoformat() if k.used_at else None,
                "used_by": k.used_by.email if k.used_by else None,
            }
            for k in royxat
        ]
    }


@router.post("/invites", status_code=status.HTTP_201_CREATED)
def invite_yarat(
    sorov: InviteRequest,
    db: DbSession = Depends(get_db),
    admin: User = Depends(admin_talab),
) -> dict:
    k = InviteCode(
        code=kod_yarat(),
        note=sorov.note,
        expires_at=datetime.now(UTC) + timedelta(days=sorov.days),
        created_by_id=admin.id,
    )
    db.add(k)
    db.commit()
    return {
        "code": k.code,
        "expires_at": k.expires_at.isoformat(),
        "note": k.note,
    }


def _topib_ol(db: DbSession, user_id: uuid.UUID) -> User:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi."
        )
    return u


@router.post("/users/{user_id}/block")
def block(
    user_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    admin: User = Depends(admin_talab),
) -> dict:
    """Foydalanuvchini bloklaydi va barcha sessiyalarini bekor qiladi.

    Sessiyalarni bekor qilish shart: aks holda bloklangan foydalanuvchi
    sessiyasi tugagunicha (2 hafta) ishlashda davom etardi.
    """
    if user_id == admin.id:
        # Oxirgi admin o'zini bloklab, tizimni boshqaruvsiz qoldirmasligi
        # kerak.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O'zingizni bloklay olmaysiz.",
        )

    u = _topib_ol(db, user_id)
    u.is_active = False
    soni = bekor_qil_barcha_sessiyalar(db, u)
    db.commit()
    return {"id": str(u.id), "is_active": False, "revoked_sessions": soni}


@router.post("/users/{user_id}/unblock")
def unblock(user_id: uuid.UUID, db: DbSession = Depends(get_db)) -> dict:
    u = _topib_ol(db, user_id)
    u.is_active = True
    db.commit()
    return {"id": str(u.id), "is_active": True}
