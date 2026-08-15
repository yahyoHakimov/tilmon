"""Sessiyalar — kirish holatini saqlash.

JWT o'rniga bazadagi sessiyalar tanlandi. Sabab: JWT ni BEKOR QILIB
bo'lmaydi. Admin foydalanuvchini bloklaganda uning tokeni muddati
tugagunicha (2 hafta) ishlashda davom etardi. Bojxona tasnifi tizimi
uchun bu qabul qilib bo'lmas.

Bazadagi sessiya esa darhol bekor qilinadi — va `is_active` tekshiruvi
har so'rovda bajarilgani uchun bloklash bir zumda kuchga kiradi.

Token cookie'da ochiq, bazada esa SHA-256 xeshi saqlanadi. Parol
xeshlashning o'sha mantiqi: baza o'g'irlansa, undagi yozuvlar bilan
hech kimning nomidan kirib bo'lmaydi.

Nega SHA-256, parollardagi kabi argon2 emas? Token 32 baytli tasodifiy
qiymat — uni lug'at bo'yicha topib bo'lmaydi, sekin xesh kerak emas.
Parol esa odam o'ylab topgan, kam entropiyali qiymat — u yerda sekinlik
himoya qiladi.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.models import User, UserSession

SESSIYA_COOKIE = "tilmon_session"

# 32 bayt = 256 bit entropiya. Taxmin qilish amalda imkonsiz.
TOKEN_BAYTLARI = 32

MAX_USER_AGENT = 255


def _xesh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def sessiya_yarat(
    db: DbSession,
    user: User,
    user_agent: str | None = None,
    ip: str | None = None,
) -> str:
    """Yangi sessiya yaratadi va cookie'ga qo'yiladigan tokenni qaytaradi.

    Token FAQAT shu yerdan qaytariladi — bazaga uning xeshi yoziladi va
    keyin tokenni hech qayerdan tiklab bo'lmaydi.
    """
    sozlama = get_settings()
    token = secrets.token_urlsafe(TOKEN_BAYTLARI)

    db.add(
        UserSession(
            token_hash=_xesh(token),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=sozlama.session_days),
            # Brauzer istalgan uzunlikdagi sarlavha yuborishi mumkin.
            user_agent=(user_agent or "")[:MAX_USER_AGENT] or None,
            ip=ip,
        )
    )
    return token


def sessiyadan_foydalanuvchi(db: DbSession, token: str | None) -> User | None:
    """Tokenga mos faol foydalanuvchini qaytaradi, yoki None.

    Uchta shart tekshiriladi: sessiya bekor qilinmagan, muddati o'tmagan,
    va foydalanuvchi bloklanmagan. Oxirgisi muhim — bloklash mavjud
    sessiyalarga ham darhol ta'sir qilishi kerak.
    """
    if not token:
        return None

    s = db.execute(
        select(UserSession).where(UserSession.token_hash == _xesh(token))
    ).scalar_one_or_none()

    if s is None or s.revoked_at is not None:
        return None
    if s.expires_at <= datetime.now(UTC):
        return None
    if not s.user.is_active:
        return None
    return s.user


def bekor_qil_sessiya(db: DbSession, token: str | None) -> None:
    """Bitta sessiyani bekor qiladi. Token topilmasa jimgina o'tadi."""
    if not token:
        return
    s = db.execute(
        select(UserSession).where(UserSession.token_hash == _xesh(token))
    ).scalar_one_or_none()
    if s is not None and s.revoked_at is None:
        s.revoked_at = datetime.now(UTC)


def bekor_qil_barcha_sessiyalar(db: DbSession, user: User) -> int:
    """Foydalanuvchining barcha sessiyalarini bekor qiladi.

    Parol o'zgartirilganda va admin bloklaganda ishlatiladi.
    """
    hozir = datetime.now(UTC)
    sessiyalar = db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
        )
    ).scalars()
    soni = 0
    for s in sessiyalar:
        s.revoked_at = hozir
        soni += 1
    return soni
