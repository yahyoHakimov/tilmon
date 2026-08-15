"""Sozlamalar — muhit o'zgaruvchilaridan.

Sirlar hech qachon kodda turmaydi. `SESSION_SECRET` va `DATABASE_URL`
majburiy: ular bo'lmasa ilova ishga tushmaydi. Bu ataylab — sukut
bo'yicha "xavfsiz emas" holatda ishlab ketish eng ko'p uchraydigan
ishlab chiqarish xatosi.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_UZUNLIGI = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(
        default="postgresql+psycopg://tilmon:tilmon_dev@127.0.0.1:55432/tilmon",
        alias="DATABASE_URL",
    )

    # Sessiya tokenlari tasodifiy va bazada xeshlangan holda saqlanadi,
    # shuning uchun bu sir imzolash uchun emas — kelajakdagi CSRF
    # tokenlari va bir martalik havolalar uchun zaxira.
    session_secret: str = Field(default="", alias="SESSION_SECRET")

    # Sessiya muddati. Bojxona tasnifi ish jarayoni — uzoq sessiya
    # qulay, lekin cheksiz emas.
    session_days: int = Field(default=14, alias="SESSION_DAYS")

    # Ishlab chiqarishda cookie faqat HTTPS orqali yuboriladi.
    # Lokal ishlab chiqishda HTTP ishlatilgani uchun o'chiriladi.
    secure_cookies: bool = Field(default=True, alias="SECURE_COOKIES")

    # Frontend qaysi manzildan kelishi mumkin (CORS va cookie domeni).
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Bir foydalanuvchi uchun soatiga nechta tasnif so'rovi.
    # OpenAI xarajatini nazorat qiladi.
    rate_limit_hourly: int = Field(default=120, alias="RATE_LIMIT_HOURLY")

    @field_validator("session_secret")
    @classmethod
    def sir_yetarli_uzunlikdami(cls, v: str) -> str:
        if v and len(v) < MIN_SECRET_UZUNLIGI:
            raise ValueError(
                f"SESSION_SECRET kamida {MIN_SECRET_UZUNLIGI} belgidan iborat "
                f"bo'lishi kerak. Yaratish: openssl rand -hex 32"
            )
        return v

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
