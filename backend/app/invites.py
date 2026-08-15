"""Taklif kodlari — yopiq beta uchun.

Kod BIR MARTA ishlatiladi. Aks holda bitta kod tarqalib ketsa, yopiq
beta ochiq bo'lib qoladi.

Kod formati odam uchun qulay: telefon orqali aytib berish oson bo'lishi
kerak, shuning uchun chalkash belgilar (0/O, 1/I/l) alfavitdan chiqarilgan.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models import InviteCode

PREFIKS = "TILMON"

# 0/O va 1/I/l chiqarilgan: telefon orqali aytib berishda chalkashmaydi.
ALFAVIT = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

GURUH_UZUNLIGI = 4
GURUHLAR = 2


class KodYaroqsiz(ValueError):
    """Taklif kodi topilmadi, ishlatilgan yoki muddati o'tgan."""


def kod_yarat() -> str:
    """Yangi taklif kodi yasaydi: TILMON-XXXX-XXXX."""
    qismlar = [
        "".join(secrets.choice(ALFAVIT) for _ in range(GURUH_UZUNLIGI))
        for _ in range(GURUHLAR)
    ]
    return f"{PREFIKS}-" + "-".join(qismlar)


def kodni_tekshir(db: DbSession, kod: str) -> InviteCode:
    """Kodni topadi va ishlatishga yaroqliligini tekshiradi.

    Kodni ishlatilgan deb BELGILAMAYDI — buni `kodni_sarfla` qiladi.
    Ajratish muhim: ro'yxatdan o'tish keyinroq boshqa sababga ko'ra
    (email band, parol zaif) rad etilishi mumkin, va bunday holatda
    kod yo'q bo'lib ketmasligi kerak.

    Raises:
        KodYaroqsiz: kod yaroqsiz bo'lsa.
    """
    normal = (kod or "").strip().upper()
    if not normal:
        raise KodYaroqsiz("Taklif kodi ko'rsatilmagan.")

    k = db.execute(
        select(InviteCode).where(InviteCode.code == normal)
    ).scalar_one_or_none()

    # Barcha yaroqsizlik holatlari uchun bir xil xabar: kod mavjudligini
    # oshkor qilmaymiz.
    if k is None:
        raise KodYaroqsiz("Taklif kodi noto'g'ri yoki muddati o'tgan.")
    if k.used_at is not None:
        raise KodYaroqsiz("Bu taklif kodi allaqachon ishlatilgan.")
    if k.expires_at is not None and k.expires_at <= datetime.now(UTC):
        raise KodYaroqsiz("Taklif kodi noto'g'ri yoki muddati o'tgan.")
    return k


def kodni_sarfla(k: InviteCode, user_id) -> None:
    """Kodni ishlatilgan deb belgilaydi.

    Faqat foydalanuvchi muvaffaqiyatli yaratilgandan KEYIN chaqiriladi.
    """
    k.used_at = datetime.now(UTC)
    k.used_by_id = user_id
