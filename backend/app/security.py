"""Parol xeshlash va parol siyosati.

Qoida bitta: parolni xeshdan qaytarib bo'lmasligi kerak. Baza o'g'irlansa
ham, undagi yozuvlardan parollarni tiklab bo'lmaydi.

Algoritm — argon2id: Password Hashing Competition g'olibi, xotira talab
qiladi va shu sababli GPU bilan brute-force qilish qimmat. bcrypt dan
farqli o'laroq parol uzunligiga chegara qo'ymaydi.
"""

from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

MIN_PAROL_UZUNLIGI = 10

# Argon2 parametrlari. Standart qiymatlardan foydalanamiz: argon2-cffi
# ularni OWASP tavsiyalariga qarab yangilab boradi.
_hasher = PasswordHasher()


class ParolZaif(ValueError):
    """Parol siyosat talablariga javob bermaydi."""


# Eng ko'p uchraydigan parollar. To'liq ro'yxat emas — bu birinchi
# himoya qatlami, uzunlik talabi bilan birga ishlaydi.
OMMABOP_PAROLLAR = frozenset(
    {
        "1234567890",
        "12345678901",
        "123456789012",
        "password123",
        "password1234",
        "parol12345",
        "parol123456",
        "qwerty123456",
        "qwertyuiop",
        "admin12345",
        "welcome123456",
        "iloveyou123",
        "letmein12345",
    }
)


def hash_password(parol: str) -> str:
    return _hasher.hash(parol)


def verify_password(xesh: str, parol: str) -> bool:
    """Parolni xeshga solishtiradi.

    Buzuq yoki bo'sh xesh xato ko'tarmaydi — `False` qaytaradi. Bazadagi
    nosoz yozuv 500 xatosiga aylanmasligi kerak.
    """
    try:
        return _hasher.verify(xesh, parol)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(xesh: str) -> bool:
    """Xesh eski parametrlar bilan yasalganmi.

    Argon2 tavsiyalari kuchayganda mavjud parollarni keyingi muvaffaqiyatli
    kirishda jimgina yangilash imkonini beradi.
    """
    try:
        return _hasher.check_needs_rehash(xesh)
    except InvalidHashError:
        return True


# Foydalanuvchi topilmaganda ham parol tekshiruvi bajarilishi uchun soxta
# xesh. Aks holda "foydalanuvchi yo'q" javobi "parol noto'g'ri" javobidan
# sezilarli tez qaytadi va hujumchi shu farq orqali qaysi emaillar
# ro'yxatdan o'tganini aniqlay oladi.
SOXTA_XESH = hash_password("tilmon-mavjud-bolmagan-foydalanuvchi-uchun")


def tekshir_parol_kuchi(parol: str, email: str | None = None) -> None:
    """Parol siyosatini tekshiradi.

    Raises:
        ParolZaif: talablarga javob bermasa. Xato matni o'zbekcha va
            foydalanuvchiga to'g'ridan-to'g'ri ko'rsatiladi.
    """
    if len(parol) < MIN_PAROL_UZUNLIGI:
        raise ParolZaif(
            f"Parol kamida {MIN_PAROL_UZUNLIGI} ta belgidan iborat bo'lishi kerak."
        )

    if parol.isdigit():
        raise ParolZaif("Parol faqat raqamlardan iborat bo'lmasligi kerak.")

    if parol.lower() in OMMABOP_PAROLLAR:
        raise ParolZaif("Bu parol juda ko'p ishlatiladi. Boshqasini tanlang.")

    if email:
        # Emailning `@` gacha bo'lgan qismi parolda uchramasligi kerak:
        # "sokhib@jett.uz" -> "sokhib".
        nom = email.split("@", 1)[0].lower()
        if len(nom) >= 3 and nom in parol.lower():
            raise ParolZaif("Parol email manzilingizga o'xshamasligi kerak.")

    # Turli belgilar sinfi bo'lishi kerak: faqat kichik harflardan iborat
    # uzun parol lug'at hujumiga zaif.
    sinflar = sum(
        bool(re.search(shablon, parol))
        for shablon in (r"[a-z]", r"[A-Z]", r"[0-9]", r"[^a-zA-Z0-9]")
    )
    if sinflar < 2:
        raise ParolZaif(
            "Parolda kamida ikki xil belgi turi bo'lishi kerak "
            "(harf, raqam yoki belgi)."
        )
