"""2-bosqich: Tasnif dvigateli.

Bu yerda OpenAI umuman yo'q. Kirish — tayyor atributlar lug'ati,
chiqish — Resolved yoki Insufficient.

Eng muhim test faylning oxirida: `test_har_qanday_toliqmas_kirish_uchun_kod_yoq`.
Qolgan hamma narsa buzilsa ham, o'sha invariant saqlanishi shart.
"""

import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.engine import Insufficient, Resolved, classify
from app.ontology import load_ontology

BLUZKA_TRIKOTAJ = {
    "mahsulot_kategoriyasi": "kiyim",
    "mato_turi": "trikotaj",
    "mahsulot_turi": "koylak_bluzka",
    "jins": "ayol",
    "tarkib": "paxta",
}


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


# --- Asosiy yo'l ------------------------------------------------------------


def test_toliq_atributlar_bilan_togri_kod(onto):
    """Loyihaning asosiy misoli."""
    n = classify(BLUZKA_TRIKOTAJ, onto)
    assert isinstance(n, Resolved)
    assert n.code == "6106 10 000 0"
    assert n.duty_rate == 10.0


def test_toqima_variant_boshqa_kod_beradi(onto):
    """Bir xil kiyim, faqat mato turi boshqa — kod butunlay boshqa."""
    n = classify({**BLUZKA_TRIKOTAJ, "mato_turi": "toqima"}, onto)
    assert isinstance(n, Resolved)
    assert n.code == "6206 30 000 0"


def test_yol_qadamlari_yozib_boriladi(onto):
    n = classify(BLUZKA_TRIKOTAJ, onto)
    atributlar = [q.attribute for q in n.path]
    assert atributlar == [
        "mahsulot_kategoriyasi",
        "mato_turi",
        "mahsulot_turi",
        "jins",
        "tarkib",
    ]


def test_atribut_tartibi_natijaga_tasir_qilmaydi(onto):
    asos = classify(BLUZKA_TRIKOTAJ, onto)
    for tartib in itertools.islice(itertools.permutations(BLUZKA_TRIKOTAJ), 12):
        aralash = {k: BLUZKA_TRIKOTAJ[k] for k in tartib}
        assert classify(aralash, onto).code == asos.code


def test_ortiqcha_atribut_eutiborsiz(onto):
    """'uzun yeng' tasnifga ta'sir qilmaydi, lekin xato ham bermaydi."""
    n = classify({**BLUZKA_TRIKOTAJ, "yeng": "uzun", "rang": "qizil"}, onto)
    assert isinstance(n, Resolved)
    assert n.code == "6106 10 000 0"
    assert set(n.unused_attributes) == {"yeng", "rang"}


# --- Jim turish: tizimning asosiy vazifasi ---------------------------------


def test_mato_turi_yoq_bolsa_kod_qaytarmaydi(onto):
    """⭐ Loyihaning mavjudlik sababi.

    "ayollar bluzkasi" — tizim javob bermasligi SHART.
    """
    n = classify(
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mahsulot_turi": "koylak_bluzka",
            "jins": "ayol",
        },
        onto,
    )
    assert isinstance(n, Insufficient)
    assert n.missing_attribute == "mato_turi"
    assert n.stopped_at == "XI"
    assert n.reason == "korsatilmagan"


def test_insufficient_natijasida_code_atributi_umuman_yoq(onto):
    """None emas — maydonning o'zi bo'lmasligi kerak.

    Shunda `natija.code` yozgan har qanday kod darhol yiqiladi, jimgina
    None tarqatmaydi.
    """
    n = classify({"mahsulot_kategoriyasi": "kiyim"}, onto)
    assert isinstance(n, Insufficient)
    assert not hasattr(n, "code")


def test_notanish_qiymat_insufficientga_olib_keladi(onto):
    """Atribut bor, lekin qiymati ontologiyada yo'q — taxmin qilinmaydi."""
    n = classify({**BLUZKA_TRIKOTAJ, "mato_turi": "bambuk"}, onto)
    assert isinstance(n, Insufficient)
    assert n.missing_attribute == "mato_turi"
    assert n.reason == "notanish_qiymat"
    assert n.provided_value == "bambuk"


def test_ziddiyatli_kirish_toxtatadi(onto):
    """'to'qima futbolka' — futbolka ta'rifi bo'yicha trikotaj, 62-bobda yo'q."""
    n = classify(
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mato_turi": "toqima",
            "mahsulot_turi": "futbolka",
            "tarkib": "paxta",
        },
        onto,
    )
    assert isinstance(n, Insufficient)
    assert n.stopped_at == "62"
    assert n.reason == "notanish_qiymat"
    assert n.provided_value == "futbolka"


def test_bosh_kirish_ildizda_toxtaydi(onto):
    n = classify({}, onto)
    assert isinstance(n, Insufficient)
    assert n.stopped_at == onto.root
    assert n.missing_attribute == "mahsulot_kategoriyasi"


def test_insufficient_qisman_yolni_saqlaydi(onto):
    """Foydalanuvchi qayergacha yetganini ko'rishi kerak."""
    n = classify(
        {"mahsulot_kategoriyasi": "kiyim", "mahsulot_turi": "koylak_bluzka"}, onto
    )
    assert [q.attribute for q in n.path] == ["mahsulot_kategoriyasi"]


def test_insufficient_savol_matnini_beradi(onto):
    """Tizim nima yetishmayotganini emas, NIMA SO'RASHNI aytishi kerak."""
    n = classify({"mahsulot_kategoriyasi": "kiyim"}, onto)
    assert n.question_uz == onto.attributes["mato_turi"].question_uz
    assert n.question_uz.strip()


# --- Nomzodlar: "6106 yoki 6206 bo'lishi mumkin" ---------------------------


def test_nomzodlar_mavjud_tarmoqlardan_olinadi(onto):
    n = classify(
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mahsulot_turi": "koylak_bluzka",
            "jins": "ayol",
        },
        onto,
    )
    assert {c.branch_value for c in n.candidates} == {"trikotaj", "toqima"}


def test_nomzodlar_qolgan_atributlar_bilan_chuqurlashtiriladi(onto):
    """Tarkib ma'lum bo'lsa, nomzod 10-xonali darajagacha aniqlanadi.

    "ayollar bluzkasi, paxta" -> 6106 10 000 0 YOKI 6206 30 000 0.
    Bu foydalanuvchiga aynan nima xavf ostidaligini ko'rsatadi.
    """
    n = classify(
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mahsulot_turi": "koylak_bluzka",
            "jins": "ayol",
            "tarkib": "paxta",
        },
        onto,
    )
    kodlar = {c.code for c in n.candidates}
    assert kodlar == {"6106 10 000 0", "6206 30 000 0"}
    assert all(c.is_final for c in n.candidates)


def test_nomzodlar_atribut_yetmasa_pozitsiya_darajasida_qoladi(onto):
    """"ayollar bluzkasi" (tarkibsiz) -> 6106 yoki 6206, 10-xonali emas."""
    n = classify(
        {
            "mahsulot_kategoriyasi": "kiyim",
            "mahsulot_turi": "koylak_bluzka",
            "jins": "ayol",
        },
        onto,
    )
    kodlar = {c.code for c in n.candidates}
    assert kodlar == {"6106", "6206"}
    assert not any(c.is_final for c in n.candidates)


# --- Rad etilganlar ---------------------------------------------------------


def test_rad_etilganlar_royxati_togri(onto):
    n = classify(BLUZKA_TRIKOTAJ, onto)
    rad_kodlar = {r.code for r in n.rejected}
    assert "62" in rad_kodlar, "to'qima tarmog'i rad etilgani ko'rsatilishi kerak"


def test_rad_etish_sababi_farqlovchiga_bogliq(onto):
    n = classify(BLUZKA_TRIKOTAJ, onto)
    r = next(r for r in n.rejected if r.code == "62")
    assert r.attribute == "mato_turi"
    assert r.required_value == "toqima"
    assert r.actual_value == "trikotaj"
    assert r.discriminator == "D_mato"


def test_tanlangan_tarmoq_rad_etilganlar_orasida_yoq(onto):
    n = classify(BLUZKA_TRIKOTAJ, onto)
    yol_targetlari = {q.target for q in n.path}
    assert not (yol_targetlari & {r.code for r in n.rejected})


def test_insufficient_holatda_ham_rad_etilganlar_bor(onto):
    """Ildizdan to'xtash nuqtasigacha rad etilganlar saqlanadi."""
    n = classify(
        {"mahsulot_kategoriyasi": "kiyim", "mahsulot_turi": "koylak_bluzka"}, onto
    )
    assert "XVI" in {r.code for r in n.rejected}


# --- Invariantlar (property-based) -----------------------------------------

_onto = load_ontology()
_ATRIBUTLAR = {nom: atr.values for nom, atr in _onto.attributes.items()}


@st.composite
def tasodifiy_atributlar(draw):
    """Har qanday atributning har qanday qismiy to'plami."""
    tanlangan = draw(
        st.lists(st.sampled_from(sorted(_ATRIBUTLAR)), unique=True, max_size=6)
    )
    return {nom: draw(st.sampled_from(_ATRIBUTLAR[nom])) for nom in tanlangan}


@given(atributlar=tasodifiy_atributlar())
@settings(max_examples=400, deadline=None)
def test_resolved_faqat_yakuniy_10_xonali_kod_bolishi_mumkin(atributlar):
    n = classify(atributlar, _onto)
    if isinstance(n, Resolved):
        assert _onto.nodes[n.code].is_final
        assert len(n.code.replace(" ", "")) == 10


@given(atributlar=tasodifiy_atributlar())
@settings(max_examples=400, deadline=None)
def test_resolved_bolsa_yoldagi_har_bir_atribut_kiritmada_bor(atributlar):
    """Dvigatel kiritmada yo'q narsani o'ylab topa olmaydi."""
    n = classify(atributlar, _onto)
    if isinstance(n, Resolved):
        for q in n.path:
            assert atributlar[q.attribute] == q.value


@given(atributlar=tasodifiy_atributlar())
@settings(max_examples=300, deadline=None)
def test_har_qanday_toliqmas_kirish_uchun_kod_yoq(atributlar):
    """Tasodifiy kirishlar uchun: yo'ldagi atribut olib tashlansa — kod yo'q."""
    n = classify(atributlar, _onto)
    if not isinstance(n, Resolved):
        return
    for q in n.path:
        kamaytirilgan = {k: v for k, v in atributlar.items() if k != q.attribute}
        assert isinstance(classify(kamaytirilgan, _onto), Insufficient)


# --- To'liq sanab chiqish (exhaustive) --------------------------------------
#
# Yuqoridagi tasodifiy test statistik: 400 misoldan atigi ~10 tasi Resolved
# bo'ladi. Quyidagilar esa BARCHA mumkin bo'lgan yo'llarni sanab chiqadi —
# tasodifga umuman tayanmaydi.


def _barcha_toliq_yollar():
    """Har bir yakuniy kodga olib boradigan minimal atribut to'plamlari."""
    nomlar = sorted(_ATRIBUTLAR)
    korilgan = {}
    for kombinatsiya in itertools.product(*(_ATRIBUTLAR[n] for n in nomlar)):
        n = classify(dict(zip(nomlar, kombinatsiya)), _onto)
        if not isinstance(n, Resolved):
            continue
        minimal = {q.attribute: q.value for q in n.path}
        korilgan[tuple(sorted(minimal.items()))] = (minimal, n.code)
    return list(korilgan.values())


TOLIQ_YOLLAR = _barcha_toliq_yollar()


def test_barcha_yakuniy_kodlarga_yetib_borish_mumkin(onto):
    """O'lik kod bo'lmasligi kerak — hech qaysi tarmoqqa yetib bo'lmasa,
    demak ontologiyada xato bor."""
    yetib_borilgan = {kod for _, kod in TOLIQ_YOLLAR}
    yakuniy = {k for k, n in onto.nodes.items() if n.is_final}
    assert yetib_borilgan == yakuniy, f"o'lik kodlar: {sorted(yakuniy - yetib_borilgan)}"


def test_toliq_yollar_soni_kutilganday():
    """Regressiya himoyasi: yo'llar soni jimgina o'zgarib ketmasin."""
    assert len(TOLIQ_YOLLAR) == 34


@pytest.mark.parametrize("minimal,kod", TOLIQ_YOLLAR, ids=lambda x: str(x)[:40])
def test_har_bir_yoldan_istalgan_atribut_olinsa_kod_yoq(minimal, kod, onto):
    """⭐⭐ Tizimning eng muhim kafolati — to'liq sanab chiqilgan holda.

    34 ta yakuniy kodning HAR BIRI uchun, unga olib borgan HAR BIR
    atributni birma-bir olib tashlaymiz. Natija hech qachon kod
    bo'lmasligi shart.

    Bu test yiqilsa — tizim taxmin qila boshlagan, demak foydalanuvchi
    jarima oladi.
    """
    assert classify(minimal, onto).code == kod
    for nom in minimal:
        kamaytirilgan = {k: v for k, v in minimal.items() if k != nom}
        natija = classify(kamaytirilgan, onto)
        assert isinstance(natija, Insufficient), (
            f"{kod}: '{nom}' noma'lum bo'lsa ham kod berildi"
        )
