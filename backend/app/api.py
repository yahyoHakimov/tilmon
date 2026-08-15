"""HTTP API — 1-4 bosqichlarni birlashtiradi.

Bu qatlamda YANGI MANTIQ YO'Q. U faqat quyidagi zanjirni chaqiradi:

    matn -> extract -> classify -> build_evidence -> assess

va natijani JSON'ga soladi.

Ikkita muhim qaror:

1. To'liqmas natijada `code` maydoni javobga UMUMAN kiritilmaydi
   (`null` emas). Shunda frontend yoki integratsiya qilingan tizim
   uni tasodifan deklaratsiyaga olib bora olmaydi.

2. Model yiqilganda ham 500 emas, 200 + "insufficient" qaytariladi.
   Nosozlik foydalanuvchi uchun "javob bera olmadim" ko'rinishida
   bo'lishi kerak, "server buzildi" emas.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.answers import merge_answers
from app.api_admin import router as admin_router
from app.api_auth import joriy_foydalanuvchi
from app.api_auth import router as auth_router
from app.config import get_settings
from app.confidence import assess
from app.engine import Resolved, classify
from app.evidence import build_evidence
from app.extractor import LLMClient, extract
from app.models import User
from app.ontology import load_ontology
from app.preflight import tekshir as tekshir_sozlama
from app.throttle import bloklanganmi, urinish_qayd_et

load_dotenv()

MAX_MATN = 2000

DISCLAIMER_UZ = (
    "Bu javob tavsiya xarakteriga ega va yuridik kuchga ega emas. "
    "Yakuniy tasnif javobgarligi deklarantda qoladi. Shubhali holatlarda "
    "bojxona organidan dastlabki qaror oling."
)

DATA_WARNING_UZ = (
    "Diqqat: javobdagi huquqiy izohlar rasmiy manbadan hali tasdiqlanmagan "
    "(sinov ma'lumotlari). Iqtiboslarni rasmiy TN VED nashri bilan "
    "solishtiring."
)

@asynccontextmanager
async def _hayot_sikli(_app: FastAPI):
    """Ishlab chiqarishda xavfsiz bo'lmagan sozlama bilan ko'tarilmaydi.

    `SECURE_COOKIES=0` yoki namunaviy `SESSION_SECRET` jimgina o'tsa,
    ilova ishlaydi-yu, himoyasi bo'lmaydi. Sekin nosozlik jim
    nosozlikdan yaxshiroq.
    """
    sozlama = get_settings()
    if sozlama.env == "production":
        for ogohlantirish in tekshir_sozlama(sozlama):
            logging.getLogger("tilmon").warning(ogohlantirish)
    yield


app = FastAPI(
    title="Tilmon — TN VED tasniflash",
    description="Asoslangan tasnif. Ma'lumot yetarli bo'lmasa, kod berilmaydi.",
    version="0.1.0",
    lifespan=_hayot_sikli,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().origins,
    # Cookie'lar cross-origin yuborilishi uchun majburiy.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)



class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_MATN)
    # Tizim bergan savollarga foydalanuvchi javoblari: {xususiyat: qiymat}.
    # Har safar TO'LIQ to'plam yuboriladi — server holat saqlamaydi.
    answers: dict[str, str] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def bosh_bolmasin(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("matn bo'sh bo'lishi mumkin emas")
        return v

    @field_validator("answers")
    @classmethod
    def javoblar_ontologiyaga_mos(cls, v: dict[str, str]) -> dict[str, str]:
        """Noto'g'ri javob 422 beradi — jimgina tashlanmaydi.

        Tekshiruv shu yerda: shunda xato mijozga aniq HTTP kodi bilan
        qaytadi va `merge_answers` ning `ValueError` i 500 ga aylanmaydi.
        """
        onto = load_ontology()
        for nom, qiymat in v.items():
            if nom not in onto.attributes:
                raise ValueError(f"noma'lum xususiyat: {nom}")
            if str(qiymat).strip().lower() not in onto.attributes[nom].values:
                raise ValueError(
                    f"'{nom}' uchun noto'g'ri qiymat: {qiymat}. "
                    f"Ruxsat etilgan: {', '.join(onto.attributes[nom].values)}"
                )
        return v


class _LazyClient:
    """Haqiqiy klientni faqat chaqiruv payti yasaydi.

    Ikki sabab:
    1. FastAPI bog'liqliklarni so'rovni tekshirishdan OLDIN hal qiladi.
       Klient shu yerda yasalsa, kalit yo'qligi noto'g'ri so'rov uchun
       ham 500 beradi — 422 o'rniga.
    2. Kalit yo'qligi `extract` ichida tutiladi va `model_ok=False` ga
       aylanadi. Ya'ni sozlama xatosi ham xuddi model nosozligi kabi
       xavfsiz kechadi: tizim taxmin qilmaydi, jim turadi.
    """

    def complete(self, system: str, user: str) -> str:
        from app.llm import default_client

        return default_client().complete(system, user)


def get_client() -> LLMClient:
    """Model klienti — testlarda `dependency_overrides` orqali almashtiriladi."""
    return _LazyClient()


@app.get("/api/healthz")
def healthz() -> dict[str, Any]:
    onto = load_ontology()
    return {
        "status": "ok",
        "nodes": len(onto.nodes),
        "discriminators": len(onto.discriminators),
        "notes": len(onto.notes),
        "ontology_version": _ontologiya_versiyasi(),
    }


@app.get("/api/attributes")
def attributes() -> dict[str, Any]:
    """UI foydalanuvchiga qanday savollar berilishi mumkinligini biladi."""
    onto = load_ontology()
    return {
        nom: {
            "label_uz": a.label_uz,
            "question_uz": a.question_uz,
            "hint_uz": a.hint_uz,
            "values": a.values,
        }
        for nom, a in onto.attributes.items()
    }


def _tasdiqlanmagan_malumot_bormi() -> bool:
    """Ontologiyada tasdiqlanmagan izoh bormi.

    Bitta bo'lsa ham ogohlantirish ko'rsatiladi: foydalanuvchi tizim
    sinov ma'lumotida ishlayotganini bilishi kerak.
    """
    return any(n.status != "official" for n in load_ontology().notes.values())


def _ontologiya_versiyasi() -> str:
    """Javob qaysi ma'lumot bazasi asosida berilganini qayd etadi.

    Hozircha oddiy hisob; rasmiy ma'lumot kelganda semantik versiyaga
    almashtiriladi.
    """
    onto = load_ontology()
    tasdiqlangan = sum(1 for n in onto.notes.values() if n.status == "official")
    return f"seed-{len(onto.nodes)}n-{len(onto.notes)}izoh-{tasdiqlangan}tasdiq"


def _limit_soatiga() -> int:
    """Soatlik so'rov limiti. Funksiya sifatida — testlarda almashtirish uchun."""
    return get_settings().rate_limit_hourly


SOAT = 3600


@app.post("/api/classify")
def classify_endpoint(
    sorov: ClassifyRequest,
    user: User = Depends(joriy_foydalanuvchi),
    client: LLMClient = Depends(get_client),
) -> dict[str, Any]:
    # So'rov limiti: OpenAI xarajatini nazorat qiladi va suiiste'molni
    # to'xtatadi. Hisob foydalanuvchi bo'yicha yuritiladi.
    kalit = f"classify:{user.id}"
    if bloklanganmi(kalit, limit=_limit_soatiga(), oyna=SOAT):
        raise HTTPException(
            status_code=429,
            detail=(
                f"Soatlik so'rov limiti ({_limit_soatiga()}) tugadi. "
                f"Keyinroq qayta urinib ko'ring."
            ),
        )
    urinish_qayd_et(kalit, oyna=SOAT)

    onto = load_ontology()

    ajratma = extract(sorov.text, onto, client)
    # Foydalanuvchi javoblari ekstraktsiya ustiga qo'yiladi. Qiymatlar
    # so'rov validatorida allaqachon tekshirilgan.
    ajratma, ziddiyatlar = merge_answers(ajratma, sorov.answers, onto)

    natija = classify(ajratma.as_dict(), onto)
    dalil = build_evidence(natija, onto)

    javob: dict[str, Any] = {
        "status": natija.status,
        "attributes": [a.model_dump() for a in ajratma.attributes.values()],
        "dropped": [d.model_dump() for d in ajratma.dropped],
        "conflicts": [z.model_dump() for z in ziddiyatlar],
        "model_ok": ajratma.model_ok,
        "evidence": dalil.model_dump(),
        "disclaimer_uz": DISCLAIMER_UZ,
        "ontology_version": _ontologiya_versiyasi(),
    }
    # Ogohlantirish JAVOBDAGI iqtiboslarga emas, tizim qaysi ma'lumotda
    # ishlayotganiga bog'liq. Aks holda eng xavfli holat — hech narsa
    # aniqlanmagan, lekin nomzod kodlar ko'rsatilgan javob — ogohlantirishsiz
    # chiqib ketardi, chunki unda iqtibos yo'q.
    if _tasdiqlanmagan_malumot_bormi():
        javob["data_warning_uz"] = DATA_WARNING_UZ

    if isinstance(natija, Resolved):
        javob |= {
            "code": natija.code,
            "title_uz": natija.title_uz,
            "duty_rate": natija.duty_rate,
            "confidence": assess(natija, ajratma).model_dump(),
        }
    else:
        # `code`, `duty_rate` va `confidence` ATAYLAB qo'shilmaydi —
        # `null` ham emas. Test buni tekshiradi.
        javob |= {
            "stopped_at": natija.stopped_at,
            "stopped_at_title_uz": natija.stopped_at_title_uz,
            "missing_attribute": natija.missing_attribute,
            "missing_attribute_label_uz": onto.attributes[
                natija.missing_attribute
            ].label_uz,
            "reason": natija.reason,
            "provided_value": natija.provided_value,
            "question_uz": natija.question_uz,
            "hint_uz": natija.hint_uz,
            "why_uz": natija.why_uz,
            "candidates": [c.model_dump() for c in natija.candidates],
        }

    return javob
