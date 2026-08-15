"""Kirish urinishlarini cheklash — brute-force ga qarshi.

Hisob xotirada yuritiladi. Bu MVP uchun ataylab tanlangan soddalik:
bitta server, bitta jarayon. Cheklovlari:

  - Server qayta ishga tushganda hisob nolga qaytadi.
  - Bir nechta ishchi jarayon bo'lsa, har biri o'z hisobini yuritadi.

Ikkalasi ham hujum oynasini kengaytiradi, lekin uni yo'q qilmaydi:
parolni taxmin qilish baribir sekinlashadi. Bir nechta serverga
o'tganda bu modul Redis yoki bazaga ko'chiriladi — interfeys
o'zgarmaydi.
"""

from __future__ import annotations

import time
from collections import defaultdict

# Nechta muvaffaqiyatsiz urinishdan keyin bloklanadi.
MAX_URINISH = 10

# Blok oynasi (soniya). Oyna ichidagi urinishlar hisoblanadi.
OYNA_SONIYA = 15 * 60

_urinishlar: dict[str, list[float]] = defaultdict(list)


def _tozalangan(kalit: str, hozir: float, oyna: float) -> list[float]:
    """Oynadan chiqib ketgan urinishlarni olib tashlaydi."""
    saqlanadi = [t for t in _urinishlar[kalit] if hozir - t < oyna]
    _urinishlar[kalit] = saqlanadi
    return saqlanadi


def soni(kalit: str, oyna: float = OYNA_SONIYA) -> int:
    """Oyna ichidagi urinishlar soni."""
    return len(_tozalangan(kalit, time.monotonic(), oyna))


def bloklanganmi(
    kalit: str, limit: int = MAX_URINISH, oyna: float = OYNA_SONIYA
) -> bool:
    return soni(kalit, oyna) >= limit


def urinish_qayd_et(kalit: str, oyna: float = OYNA_SONIYA) -> None:
    """Urinishni qayd etadi."""
    hozir = time.monotonic()
    _tozalangan(kalit, hozir, oyna)
    _urinishlar[kalit].append(hozir)


def hisobni_tozala(kalit: str) -> None:
    """Muvaffaqiyatli kirishdan keyin chaqiriladi."""
    _urinishlar.pop(kalit, None)


def tozala_urinishlar() -> None:
    """Barcha hisoblarni tozalaydi — testlar uchun."""
    _urinishlar.clear()
