"""Ishga tushirishdan oldingi sozlama tekshiruvi.

Ishlab chiqarishdagi eng ko'p uchraydigan xato — sozlamani unutish.
`SECURE_COOKIES=0` qolib ketsa, sessiya ochiq kanalda ketadi. Ilova
baribir ishlaydi, hech narsa yiqilmaydi — shunchaki himoya yo'q.

Bunday jim nosozlikning oldini olish uchun `ENV=production` da
xavfsiz bo'lmagan sozlama ISHGA TUSHISHNI TO'XTATADI.

Sekin nosozlik jim nosozlikdan yaxshiroq.
"""

from __future__ import annotations

from app.config import Settings

# `.env.example` va qo'llanmalardan ko'chirilishi mumkin bo'lgan qiymatlar.
NAMUNAVIY_SIRLAR = frozenset(
    {"o'zgartiring", "changeme", "change-me", "secret", "sir", "xxx", "test"}
)

# Ishlab chiqish paroli — `.env.example` da turadi, serverga tushmasligi kerak.
ISHLAB_CHIQISH_PAROLLARI = frozenset({"tilmon_dev", "postgres", "password", "parol"})


class SozlamaXavfli(RuntimeError):
    """Ishlab chiqarish uchun xavfsiz bo'lmagan sozlama."""


def _sir_zaifmi(sir: str) -> bool:
    past = sir.lower()
    if any(n in past for n in NAMUNAVIY_SIRLAR):
        return True
    # Bir xil belgidan iborat qator ("aaa…") — tasodifiy emas.
    return len(set(sir)) < 8


def _baza_paroli(url: str) -> str | None:
    """DATABASE_URL dan parolni ajratadi. Topilmasa None."""
    if "@" not in url or "://" not in url:
        return None
    kredential = url.split("://", 1)[1].split("@", 1)[0]
    if ":" not in kredential:
        return None
    return kredential.split(":", 1)[1]


def tekshir(sozlama: Settings) -> list[str]:
    """Sozlamani tekshiradi.

    Returns:
        Ogohlantirishlar ro'yxati — ular ishga tushishga to'sqinlik qilmaydi.

    Raises:
        SozlamaXavfli: xavfsizlikka tegadigan muammo topilsa. BARCHA
            muammolar bitta xatoda ko'rsatiladi — har safar bittadan
            tuzatib, qayta ishga tushirish vaqt yo'qotish.
    """
    muammolar: list[str] = []
    ogohlantirishlar: list[str] = []

    # --- Cookie ---
    if not sozlama.secure_cookies:
        muammolar.append(
            "SECURE_COOKIES=0 — sessiya cookie'si HTTP orqali ham yuboriladi.\n"
            "    Tarmoqni tinglagan har kim uni o'qib, foydalanuvchi nomidan "
            "kira oladi.\n"
            "    Tuzatish: SECURE_COOKIES=1"
        )

    # --- Sessiya siri ---
    if not sozlama.session_secret.strip():
        muammolar.append(
            "SESSION_SECRET bo'sh.\n"
            "    Tuzatish: openssl rand -hex 32"
        )
    elif _sir_zaifmi(sozlama.session_secret):
        muammolar.append(
            "SESSION_SECRET namunaviy yoki taxmin qilinadigan qiymat.\n"
            "    Tuzatish: openssl rand -hex 32"
        )

    # --- Ma'lumotlar bazasi ---
    url = sozlama.database_url
    if not url.startswith("postgresql"):
        muammolar.append(
            f"DATABASE_URL Postgres emas: {url.split('://')[0]}\n"
            "    Tizim Postgres uchun yozilgan (UUID, timezone'li vaqt)."
        )
    else:
        parol = _baza_paroli(url)
        if not parol:
            muammolar.append(
                "DATABASE_URL da parol yo'q.\n"
                "    Tuzatish: postgresql+psycopg://tilmon:<parol>@127.0.0.1:5432/tilmon"
            )
        elif parol in ISHLAB_CHIQISH_PAROLLARI:
            muammolar.append(
                f"DATABASE_URL da ishlab chiqish paroli ishlatilgan: '{parol}'\n"
                "    Tuzatish: openssl rand -base64 24"
            )

    # --- CORS ---
    origins = sozlama.origins
    if not origins or origins == ["*"]:
        muammolar.append(
            "ALLOWED_ORIGINS bo'sh yoki '*'.\n"
            "    Tuzatish: ALLOWED_ORIGINS=https://sizning-domen.uz"
        )
    else:
        for o in origins:
            if "localhost" in o or "127.0.0.1" in o:
                muammolar.append(
                    f"ALLOWED_ORIGINS da lokal manzil qolgan: {o}\n"
                    "    Tuzatish: faqat haqiqiy domenni qoldiring."
                )
            elif not o.startswith("https://"):
                muammolar.append(
                    f"ALLOWED_ORIGINS da https bo'lmagan manzil: {o}\n"
                    "    `Secure` cookie HTTP orqali yuborilmaydi — "
                    "kirish umuman ishlamaydi.\n"
                    "    Tuzatish: https:// ishlating."
                )

    # --- Ogohlantirishlar: ishga tushishga to'sqinlik qilmaydi ---
    if not sozlama.openai_api_key.strip():
        ogohlantirishlar.append(
            "OPENAI_API_KEY yo'q — erkin matn tahlil qilinmaydi. "
            "Javob tugmalari orqali qo'lda tasnif ishlaydi."
        )

    if muammolar:
        raise SozlamaXavfli(
            "Ishlab chiqarish sozlamasida "
            f"{len(muammolar)} ta muammo topildi:\n\n"
            + "\n\n".join(f"  {i}. {m}" for i, m in enumerate(muammolar, 1))
            + "\n"
        )

    return ogohlantirishlar
