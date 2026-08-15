"""Frontend testlari uchun fixture yasaydi.

Backend javob shakli o'zgarganda ishga tushiring:

    uv run python scripts/gen_fixtures.py

`test_frontend_fixture_kontrakt_bilan_mos` testi fixture eskirganini
aytadi, bu skript esa uni yangilaydi.
"""

import json
import pathlib
import uuid
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.api import app, get_client  # noqa: E402
from app.api_auth import joriy_foydalanuvchi  # noqa: E402

TOZA = {
    "mahsulot_kategoriyasi": {"value": "kiyim", "source": "inferred", "evidence": "bluzka"},
    "mato_turi": {"value": "trikotaj", "source": "stated", "evidence": "trikotaj"},
    "mahsulot_turi": {"value": "koylak_bluzka", "source": "stated", "evidence": "bluzkasi"},
    "jins": {"value": "ayol", "source": "stated", "evidence": "ayollar"},
    "tarkib": {"value": "paxta", "source": "stated", "evidence": "100% paxta"},
}
QISMLI = {k: v for k, v in TOZA.items() if k != "mato_turi"}

HOLATLAR = [
    ("resolved", TOZA, "ayollar bluzkasi, 100% paxta, trikotaj, uzun yeng"),
    ("insufficient", QISMLI, "ayollar bluzkasi, 100% paxta"),
    ("empty", {}, "salom"),
]


class _SoxtaUser:
    """Fixture yasashda auth talab qilinmaydi — bu yerda tasnif javobining
    SHAKLI muhim, kirish tizimi emas."""

    id = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
    email = "fixture@example.uz"
    role = "user"
    is_active = True


class _Fake:
    def __init__(self, atributlar):
        self.atributlar = atributlar

    def complete(self, system, user):
        return json.dumps({"attributes": self.atributlar})


def main() -> None:
    natija = {}
    for nom, atributlar, matn in HOLATLAR:
        app.dependency_overrides[get_client] = lambda a=atributlar: _Fake(a)
        app.dependency_overrides[joriy_foydalanuvchi] = _SoxtaUser
        natija[nom] = TestClient(app).post("/api/classify", json={"text": matn}).json()
    app.dependency_overrides.clear()

    yol = pathlib.Path(__file__).resolve().parents[2] / "web/src/__tests__/fixtures.json"
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(
        json.dumps(natija, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Yozildi: {yol}")


if __name__ == "__main__":
    main()
