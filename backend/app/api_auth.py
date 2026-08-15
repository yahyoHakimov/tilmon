"""Kirish endpointlari: /api/auth/*

Ikkita qaror bu faylni belgilaydi:

1. **Xato javoblari bir xil.** "Bunday email yo'q", "parol noto'g'ri" va
   "foydalanuvchi bloklangan" — uchalasi ham AYNAN bir xil 401 beradi.
   Aks holda hujumchi javob farqidan qaysi emaillar ro'yxatdan
   o'tganini aniqlay oladi.

2. **Foydalanuvchi topilmasa ham parol tekshiriladi.** Soxta xesh bilan.
   Aks holda "email yo'q" javobi sezilarli tez qaytadi va vaqt farqi
   o'sha ma'lumotni oshkor qiladi.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth import (
    SESSIYA_COOKIE,
    bekor_qil_sessiya,
    sessiya_yarat,
    sessiyadan_foydalanuvchi,
)
from app.config import get_settings
from app.db import get_db
from app.invites import KodYaroqsiz, kodni_sarfla, kodni_tekshir
from app.models import User
from app.security import (
    SOXTA_XESH,
    ParolZaif,
    hash_password,
    tekshir_parol_kuchi,
    verify_password,
)
from app.throttle import bloklanganmi, hisobni_tozala, urinish_qayd_et

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Barcha kirish xatolari uchun yagona matn. O'zgartirilsa, testlar
# yiqiladi — bu ataylab.
KIRISH_XATOSI = "Email yoki parol noto'g'ri."


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=500)


class UserOut(BaseModel):
    """Foydalanuvchining ochiq ko'rinishi.

    `password_hash` bu yerda YO'Q va bo'lmasligi kerak. Model to'g'ridan-
    to'g'ri serializatsiya qilinmaydi — faqat shu sxema orqali chiqadi.
    """

    id: str
    email: str
    role: str
    created_at: datetime


def _chiqar(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "role": u.role,
        "created_at": u.created_at.isoformat(),
    }


def _cookie_ornat(response: Response, token: str) -> None:
    sozlama = get_settings()
    response.set_cookie(
        SESSIYA_COOKIE,
        token,
        max_age=sozlama.session_days * 24 * 3600,
        # JavaScript o'qiy olmaydi — XSS da sessiya o'g'irlanmasligi uchun.
        httponly=True,
        # Faqat HTTPS orqali (ishlab chiqarishda).
        secure=sozlama.secure_cookies,
        # Lax: boshqa saytdan kelgan POST so'rovlarga cookie qo'shilmaydi,
        # lekin oddiy havola bo'yicha o'tishda saqlanadi. CSRF ning
        # asosiy vektorini yopadi va UX ni buzmaydi.
        samesite="lax",
        path="/",
    )


# --- Joriy foydalanuvchi bog'liqliklari ------------------------------------


def joriy_foydalanuvchi_ixtiyoriy(
    request: Request, db: DbSession = Depends(get_db)
) -> User | None:
    return sessiyadan_foydalanuvchi(db, request.cookies.get(SESSIYA_COOKIE))


def joriy_foydalanuvchi(
    user: User | None = Depends(joriy_foydalanuvchi_ixtiyoriy),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kirish talab qilinadi.",
        )
    return user


def admin_talab(user: User = Depends(joriy_foydalanuvchi)) -> User:
    if user.role != "admin":
        # 404 emas, 403: foydalanuvchi kirgan, lekin huquqi yo'q.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu amal uchun administrator huquqi kerak.",
        )
    return user


# --- Endpointlar -----------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=500)
    invite_code: str = Field(min_length=1, max_length=64)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    sorov: RegisterRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
) -> dict:
    """Yopiq beta: taklif kodisiz ro'yxatdan o'tib bo'lmaydi.

    Tekshiruvlar tartibi muhim: kod OXIRIDA sarflanadi. Aks holda
    email band yoki parol zaif bo'lgan urinish taklif kodini
    yo'q qilib yuborardi.
    """
    email = sorov.email.strip().lower()

    try:
        kod = kodni_tekshir(db, sorov.invite_code)
    except KodYaroqsiz as xato:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(xato)
        ) from xato

    bor = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if bor is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu email allaqachon ro'yxatdan o'tgan.",
        )

    try:
        tekshir_parol_kuchi(sorov.password, email=email)
    except ParolZaif as xato:
        raise HTTPException(
            status_code=422, detail=str(xato)
        ) from xato

    u = User(email=email, password_hash=hash_password(sorov.password))
    db.add(u)
    db.flush()

    kodni_sarfla(kod, u.id)

    u.last_login_at = datetime.now(UTC)
    token = sessiya_yarat(
        db,
        u,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.commit()

    _cookie_ornat(response, token)
    return _chiqar(u)


@router.post("/login")
def login(
    sorov: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
) -> dict:
    email = sorov.email.strip().lower()

    if bloklanganmi(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Juda ko'p muvaffaqiyatsiz urinish. "
                "15 daqiqadan keyin qayta urinib ko'ring."
            ),
        )

    u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    # Foydalanuvchi topilmasa ham parol tekshiriladi: javob vaqti
    # mavjud foydalanuvchinikiga yaqin bo'lishi kerak.
    xesh = u.password_hash if u is not None else SOXTA_XESH
    parol_togri = verify_password(xesh, sorov.password)

    if u is None or not parol_togri or not u.is_active:
        urinish_qayd_et(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=KIRISH_XATOSI
        )

    hisobni_tozala(email)
    u.last_login_at = datetime.now(UTC)

    token = sessiya_yarat(
        db,
        u,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.commit()

    _cookie_ornat(response, token)
    return _chiqar(u)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request, response: Response, db: DbSession = Depends(get_db)
) -> Response:
    bekor_qil_sessiya(db, request.cookies.get(SESSIYA_COOKIE))
    db.commit()
    # Kirmagan holatda ham 204 — kirgan-kirmaganini oshkor qilmaydi.
    response.delete_cookie(SESSIYA_COOKIE, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=response.headers)


@router.get("/me")
def me(user: User = Depends(joriy_foydalanuvchi)) -> dict:
    return _chiqar(user)
