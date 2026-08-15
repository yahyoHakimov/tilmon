"""7-bosqich: Oltin to'plam — regressiya himoyasi.

`golden.yaml` — tizimning xatti-harakati haqidagi SHARTNOMA. Har bir
misol qo'lda yozilgan va kutilgan natijasi belgilangan.

Har bir misolda ikkita kirish shakli bor:

  `atributlar` — dvigatelga to'g'ridan-to'g'ri beriladi. Deterministik,
                 modelsiz, CI'da doim ishlaydi.
  `kirish`     — haqiqiy foydalanuvchi matni. `-m live` bilan haqiqiy
                 model orqali o'tkaziladi.

Shunday qilib bir xil kutilgan natija ikki darajada tekshiriladi:
mantiq to'g'rimi, va model o'sha mantiqqa to'g'ri ma'lumot beradimi.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from app.engine import Insufficient, Resolved, classify
from app.extractor import extract
from app.ontology import load_ontology

GOLDEN_PATH = Path(__file__).parent / "golden.yaml"
MIN_JIM_MISOL = 15


def _yukla():
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


OLTIN = _yukla()
KOD_MISOLLAR = [m for m in OLTIN if m["kutilgan"]["status"] == "resolved"]
JIM_MISOLLAR = [m for m in OLTIN if m["kutilgan"]["status"] == "insufficient"]


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


def _id(m):
    return f"{m['id']}:{m['kirish'][:34]}"


# --- To'plamning o'z sifati -------------------------------------------------


def test_oltin_toplam_bosh_emas():
    assert len(OLTIN) >= 40


def test_idlar_unikal():
    idlar = [m["id"] for m in OLTIN]
    assert len(idlar) == len(set(idlar))


def test_har_bir_misol_toliq():
    for m in OLTIN:
        assert m["kirish"].strip(), f"{m['id']}: kirish matni yo'q"
        assert m["izoh"].strip(), f"{m['id']}: izoh yo'q"
        assert isinstance(m["atributlar"], dict), f"{m['id']}: atributlar lug'at emas"
        assert m["kutilgan"]["status"] in ("resolved", "insufficient")


def test_kamida_15_ta_jim_turish_misoli():
    """⭐ Muvozanat kafolati.

    Faqat "to'g'ri javob" misollari bilan to'ldirilgan to'plam
    xavfli: u tizimni ko'proq javob berishga undaydi. Jim turish
    misollari kamida shuncha bo'lishi shart.
    """
    assert len(JIM_MISOLLAR) >= MIN_JIM_MISOL, (
        f"faqat {len(JIM_MISOLLAR)} ta jim turish misoli bor, "
        f"kamida {MIN_JIM_MISOL} ta kerak"
    )


def test_kamida_15_ta_kod_misoli():
    """Teskari muvozanat: tizim shunchaki "hech qachon javob bermaydigan"
    bo'lib qolmasligi kerak."""
    assert len(KOD_MISOLLAR) >= MIN_JIM_MISOL


def test_kutilgan_kodlar_ontologiyada_mavjud(onto):
    for m in KOD_MISOLLAR:
        kod = m["kutilgan"]["code"]
        assert kod in onto.nodes, f"{m['id']}: '{kod}' ontologiyada yo'q"
        assert onto.nodes[kod].is_final


def test_kutilgan_atributlar_ontologiyada_elon_qilingan(onto):
    for m in JIM_MISOLLAR:
        atr = m["kutilgan"]["missing"]
        assert atr in onto.attributes, f"{m['id']}: '{atr}' atributi yo'q"


def test_toplam_barcha_boblarni_qamraydi():
    kodlar = [m["kutilgan"]["code"] for m in KOD_MISOLLAR]
    for bob in ("6103", "6104", "6105", "6106", "6109", "6110",
                "6203", "6204", "6205", "6206",
                "8471", "8504", "8517", "8544"):
        assert any(k.startswith(bob) for k in kodlar), f"{bob} qamralmagan"


# --- ⭐ Asosiy regressiya testlari ------------------------------------------


@pytest.mark.parametrize("m", KOD_MISOLLAR, ids=_id)
def test_kod_misollari_kutilgan_kodni_beradi(m, onto):
    natija = classify(m["atributlar"], onto)
    assert isinstance(natija, Resolved), (
        f"{m['id']}: kod kutilgan edi, lekin tizim jim turdi "
        f"({getattr(natija, 'missing_attribute', '?')})"
    )
    assert natija.code == m["kutilgan"]["code"]


@pytest.mark.parametrize("m", JIM_MISOLLAR, ids=_id)
def test_jim_turishi_kerak_misollar_HECH_QACHON_kod_bermaydi(m, onto):
    """⭐⭐ To'plamning eng muhim yarmi.

    Bu test yiqilsa — tizim taxmin qila boshlagan. Foydalanuvchi
    taxminni deklaratsiyaga yozadi va jarima oladi.
    """
    natija = classify(m["atributlar"], onto)
    assert isinstance(natija, Insufficient), (
        f"{m['id']}: tizim jim turishi kerak edi, lekin "
        f"'{getattr(natija, 'code', '?')}' kodini berdi"
    )
    assert natija.missing_attribute == m["kutilgan"]["missing"]
    if "reason" in m["kutilgan"]:
        assert natija.reason == m["kutilgan"]["reason"]


# --- Haqiqiy model bilan (live) --------------------------------------------

live = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY o'rnatilmagan"
)


@pytest.mark.live
@live
@pytest.mark.parametrize("m", JIM_MISOLLAR, ids=_id)
def test_live_jim_misollar_matndan_ham_kod_bermaydi(m, onto):
    """⭐ Eng qimmatli live test.

    Bu yerda model taxminga eng ko'p moyil bo'ladi: matn to'liqmas,
    lekin u "foydali bo'lishni" xohlaydi. Prompt uni to'xtatishi kerak.
    """
    ajratma = extract(m["kirish"], onto)
    natija = classify(ajratma.as_dict(), onto)
    assert isinstance(natija, Insufficient), (
        f"{m['id']}: '{m['kirish']}' uchun model yetishmayotgan ma'lumotni "
        f"taxmin qildi -> {getattr(natija, 'code', '?')}"
    )


@pytest.mark.live
@live
@pytest.mark.parametrize("m", KOD_MISOLLAR, ids=_id)
def test_live_kod_misollari_matndan_ham_ishlaydi(m, onto):
    ajratma = extract(m["kirish"], onto)
    natija = classify(ajratma.as_dict(), onto)
    assert isinstance(natija, Resolved), (
        f"{m['id']}: '{m['kirish']}' -> model yetarli ma'lumot ajrata olmadi "
        f"(yetishmagan: {getattr(natija, 'missing_attribute', '?')})"
    )
    assert natija.code == m["kutilgan"]["code"]
