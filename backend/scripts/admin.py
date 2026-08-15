"""Boshqaruv skripti — birinchi admin va taklif kodlari uchun.

Bu "tovuq va tuxum" muammosini yechadi: admin endpointlariga kirish
uchun admin kerak, lekin birinchi adminni yaratish uchun endpoint yo'q.

Ishlatish:

    uv run python scripts/admin.py create-admin sokhib@jett.uz
    uv run python scripts/admin.py invite --note "Aziz aka" --count 5
    uv run python scripts/admin.py users
    uv run python scripts/admin.py invites
    uv run python scripts/admin.py block user@example.uz
    uv run python scripts/admin.py reset-password sokhib@jett.uz

Parol terminalga yozilmaydi — `getpass` orqali yashirin so'raladi va
buyruqlar tarixiga tushmaydi.
"""

from __future__ import annotations

import argparse
import getpass
import pathlib
import sys
from datetime import UTC, datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.auth import bekor_qil_barcha_sessiyalar  # noqa: E402
from app.db import get_sessionmaker  # noqa: E402
from app.invites import kod_yarat  # noqa: E402
from app.models import InviteCode, User  # noqa: E402
from app.security import (  # noqa: E402
    ParolZaif,
    hash_password,
    tekshir_parol_kuchi,
)


def _parol_sora(email: str) -> str:
    """Parolni ikki marta so'raydi va siyosatga solishtiradi."""
    while True:
        p1 = getpass.getpass("Parol: ")
        p2 = getpass.getpass("Parolni takrorlang: ")
        if p1 != p2:
            print("Parollar mos kelmadi. Qayta urinib ko'ring.\n")
            continue
        try:
            tekshir_parol_kuchi(p1, email=email)
        except ParolZaif as xato:
            print(f"{xato}\n")
            continue
        return p1


def _topib_ol(db, email: str) -> User:
    u = db.execute(
        select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()
    if u is None:
        sys.exit(f"Foydalanuvchi topilmadi: {email}")
    return u


def create_admin(args) -> None:
    email = args.email.strip().lower()
    with get_sessionmaker()() as db:
        if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
            sys.exit(f"Bu email allaqachon ro'yxatdan o'tgan: {email}")

        parol = _parol_sora(email)
        db.add(User(email=email, password_hash=hash_password(parol), role="admin"))
        db.commit()
    print(f"✓ Administrator yaratildi: {email}")


def invite(args) -> None:
    with get_sessionmaker()() as db:
        kodlar = []
        for _ in range(args.count):
            k = InviteCode(
                code=kod_yarat(),
                note=args.note,
                expires_at=datetime.now(UTC) + timedelta(days=args.days),
            )
            db.add(k)
            kodlar.append(k.code)
        db.commit()

    print(f"✓ {len(kodlar)} ta taklif kodi ({args.days} kun amal qiladi):\n")
    for k in kodlar:
        print(f"    {k}")
    print()


def users(args) -> None:
    with get_sessionmaker()() as db:
        royxat = db.execute(select(User).order_by(User.created_at)).scalars().all()

    if not royxat:
        print("Foydalanuvchilar yo'q.")
        return
    print(f"{'EMAIL':<34} {'ROL':<7} {'HOLAT':<12} OXIRGI KIRISH")
    print("-" * 80)
    for u in royxat:
        holat = "faol" if u.is_active else "BLOKLANGAN"
        oxirgi = (
            u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else "—"
        )
        print(f"{u.email:<34} {u.role:<7} {holat:<12} {oxirgi}")


def invites(args) -> None:
    with get_sessionmaker()() as db:
        royxat = (
            db.execute(select(InviteCode).order_by(InviteCode.created_at))
            .scalars()
            .all()
        )
        # `used_by` bog'lanishi sessiya yopilgunicha o'qilishi kerak.
        satrlar = [
            (
                k.code,
                k.note or "—",
                "ishlatilgan" if k.used_at else "bo'sh",
                k.used_by.email if k.used_by else "—",
            )
            for k in royxat
        ]

    if not satrlar:
        print("Taklif kodlari yo'q.")
        return
    print(f"{'KOD':<20} {'IZOH':<20} {'HOLAT':<13} KIM ISHLATDI")
    print("-" * 80)
    for kod, izoh, holat, kim in satrlar:
        print(f"{kod:<20} {izoh:<20} {holat:<13} {kim}")


def block(args) -> None:
    with get_sessionmaker()() as db:
        u = _topib_ol(db, args.email)
        u.is_active = False
        soni = bekor_qil_barcha_sessiyalar(db, u)
        db.commit()
    print(f"✓ {u.email} bloklandi, {soni} ta sessiya bekor qilindi.")


def unblock(args) -> None:
    with get_sessionmaker()() as db:
        u = _topib_ol(db, args.email)
        u.is_active = True
        db.commit()
    print(f"✓ {u.email} bloki yechildi.")


def reset_password(args) -> None:
    with get_sessionmaker()() as db:
        u = _topib_ol(db, args.email)
        u.password_hash = hash_password(_parol_sora(u.email))
        # Parol o'zgarganda barcha sessiyalar bekor qilinadi: agar parol
        # o'g'irlangani uchun almashtirilayotgan bo'lsa, eski sessiyalar
        # ham to'xtashi kerak.
        soni = bekor_qil_barcha_sessiyalar(db, u)
        db.commit()
    print(f"✓ Parol yangilandi, {soni} ta sessiya bekor qilindi.")


def main() -> None:
    p = argparse.ArgumentParser(description="Tilmon boshqaruv skripti")
    sub = p.add_subparsers(dest="buyruq", required=True)

    c = sub.add_parser("create-admin", help="Birinchi administratorni yaratish")
    c.add_argument("email")
    c.set_defaults(func=create_admin)

    c = sub.add_parser("invite", help="Taklif kodi yaratish")
    c.add_argument("--note", default=None, help="Kim uchun (eslatma)")
    c.add_argument("--count", type=int, default=1)
    c.add_argument("--days", type=int, default=30)
    c.set_defaults(func=invite)

    sub.add_parser("users", help="Foydalanuvchilar ro'yxati").set_defaults(func=users)
    sub.add_parser("invites", help="Taklif kodlari ro'yxati").set_defaults(func=invites)

    c = sub.add_parser("block", help="Foydalanuvchini bloklash")
    c.add_argument("email")
    c.set_defaults(func=block)

    c = sub.add_parser("unblock", help="Blokni yechish")
    c.add_argument("email")
    c.set_defaults(func=unblock)

    c = sub.add_parser("reset-password", help="Parolni almashtirish")
    c.add_argument("email")
    c.set_defaults(func=reset_password)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
