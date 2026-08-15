"""Ma'lumotlar bazasi ulanishi.

Tizim yadrosi (ontologiya, dvigatel, asos zanjiri, ekstraktor) bazaga
UMUMAN bog'liq emas — baza faqat foydalanuvchilar, sessiyalar va taklif
kodlari uchun. Bu ajratish ataylab: tasnif mantiqini har qanday muhitda,
infratuzilmasiz test qilib bo'ladi.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine():
    sozlama = get_settings()
    return create_engine(
        sozlama.database_url,
        # Ulanishni ishlatishdan oldin tekshiradi: uzoq turgan ulanish
        # server tomonidan yopilgan bo'lsa, jimgina qayta ulanadi.
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def get_sessionmaker():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI bog'liqligi: so'rov davomida ochiq sessiya."""
    sess = get_sessionmaker()()
    try:
        yield sess
    finally:
        sess.close()
