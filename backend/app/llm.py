"""OpenAI klienti — `LLMClient` shartnomasining haqiqiy implementatsiyasi.

Bu modul ataylab yupqa. Butun himoya `extractor._sanitize` da: bu yerda
qanday javob kelishidan qat'i nazar, u ontologiya filtridan o'tadi.

Shu sababli bu faylda test kam — uni almashtirish provayder almashtirish
bilan barobar, tizimning xavfsizlik xususiyatlariga ta'sir qilmaydi.
"""

from __future__ import annotations

import os
from functools import lru_cache

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 20.0


class OpenAIClient:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        from openai import OpenAI

        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self._client = OpenAI(
            api_key=api_key or os.environ["OPENAI_API_KEY"], timeout=timeout
        )

    def complete(self, system: str, user: str) -> str:
        javob = self._client.chat.completions.create(
            model=self.model,
            # temperature=0: bir xil kiritma bir xil natija berishi kerak.
            # Bojxona tasnifida tasodifiylik joyi yo'q.
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return javob.choices[0].message.content or ""


@lru_cache(maxsize=1)
def default_client() -> OpenAIClient:
    """Muhit o'zgaruvchilaridan klient yasaydi.

    Kalit yo'q bo'lsa KeyError ko'taradi — bu `extract` da tutiladi va
    `model_ok=False` ga aylanadi, ya'ni tizim taxmin qilmaydi.
    """
    return OpenAIClient()
