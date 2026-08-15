"""Ma'lumotlar bazasi modellari: foydalanuvchi, sessiya, taklif kodi.

Ikkita xavfsizlik qarori bu yerda kod bilan mustahkamlangan:

1. `users` jadvalida ochiq parol ustuni YO'Q — faqat `password_hash`.
2. `sessions` jadvalida ochiq token ustuni YO'Q — faqat `token_hash`.
   Baza o'g'irlansa, undagi yozuvlar bilan hech kimning nomidan kirib
   bo'lmaydi.

Ikkalasi ham test bilan tekshiriladi (`test_models.py`).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db import Base

ROLLAR = ("user", "admin")


def _hozir() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN " + str(ROLLAR).replace("'", "'"), name="ck_users_role"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Email normallashtirilgan holda saqlanadi (kichik harf, probelsiz),
    # shuning uchun oddiy unikal indeks registrga sezgir emaslikni
    # ta'minlaydi.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_hozir, server_default=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    @validates("email")
    def _normalize_email(self, _key: str, qiymat: str) -> str:
        return qiymat.strip().lower()

    def __repr__(self) -> str:  # pragma: no cover — faqat nosozlik tuzatish
        return f"<User {self.email} ({self.role})>"


class UserSession(Base):
    """Kirish sessiyasi.

    Cookie'dagi tokenning O'ZI bu yerda saqlanmaydi — faqat SHA-256 xeshi.
    Tekshirishda kelgan token xeshlanadi va shu ustun bo'yicha qidiriladi.
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_hozir, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Shubhali faollikni tekshirish uchun. Shaxsiy ma'lumot bo'lgani
    # uchun sessiya muddati tugagach tozalanadi.
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class InviteCode(Base):
    """Yopiq beta uchun taklif kodi.

    Bir marta ishlatiladi. Kod ochiq saqlanadi — admin uni ko'rib,
    foydalanuvchiga uzatishi kerak. Xavf past: kod faqat ro'yxatdan
    o'tish huquqini beradi, hech qanday ma'lumotga kirish bermaydi.
    """

    __tablename__ = "invite_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_hozir, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    used_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    used_by: Mapped[User | None] = relationship(foreign_keys=[used_by_id])
