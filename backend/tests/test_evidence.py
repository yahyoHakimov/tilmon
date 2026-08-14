"""3-bosqich: Asos zanjiri va iqtibos haqiqiyligi.

Loyihaning 2-talabi: "Asos haqiqiy. Model o'ylab topgan gapdan emas."

Bu fayldagi testlar shuni kafolatlaydi: javobdagi HAR BIR huquqiy matn
parchasi `notes.yaml` da mavjud yozuvning AYNAN nusxasi. Substring emas,
o'xshash emas — aynan teng. Shablon bilan yasalgan, qisqartirilgan yoki
"tushunarli qilib qayta yozilgan" matn testni yiqitadi.
"""

import pytest

from app.engine import classify
from app.evidence import build_evidence
from app.ontology import load_ontology

BLUZKA_TRIKOTAJ = {
    "mahsulot_kategoriyasi": "kiyim",
    "mato_turi": "trikotaj",
    "mahsulot_turi": "koylak_bluzka",
    "jins": "ayol",
    "tarkib": "paxta",
}

BLUZKA_TOLIQMAS = {
    "mahsulot_kategoriyasi": "kiyim",
    "mahsulot_turi": "koylak_bluzka",
    "jins": "ayol",
}


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


@pytest.fixture
def dalil(onto):
    return build_evidence(classify(BLUZKA_TRIKOTAJ, onto), onto)


@pytest.fixture
def dalil_toliqmas(onto):
    return build_evidence(classify(BLUZKA_TOLIQMAS, onto), onto)


# --- Zanjir tuzilishi -------------------------------------------------------


def test_har_bir_qadam_asos_matniga_ega(dalil):
    assert dalil.steps
    for q in dalil.steps:
        assert q.citations, f"{q.attribute}: iqtibossiz qadam"


def test_asos_zanjiri_qadamlar_tartibida(dalil, onto):
    natija = classify(BLUZKA_TRIKOTAJ, onto)
    assert [q.attribute for q in dalil.steps] == [q.attribute for q in natija.path]


def test_insufficient_holatda_ham_qisman_zanjir_bor(dalil_toliqmas):
    """Foydalanuvchi qayergacha yetganini va NEGA to'xtaganini ko'rishi kerak."""
    assert len(dalil_toliqmas.steps) == 1
    assert dalil_toliqmas.steps[0].attribute == "mahsulot_kategoriyasi"


def test_rad_etish_ham_asosga_ega(dalil):
    """"6206 rad etildi" degani yetarli emas — nega, degan savolga javob kerak."""
    r = next(r for r in dalil.rejections if r.code == "62")
    assert r.citations


# --- ⭐ Iqtibos haqiqiyligi -------------------------------------------------


def test_asos_matni_bazadagi_matn_bilan_AYNAN_teng(dalil, onto):
    for q in dalil.steps:
        for c in q.citations:
            assert c.text == onto.notes[c.note_id].text
            assert c.ref == onto.notes[c.note_id].ref


def test_javobdagi_har_bir_iqtibos_notes_yamlda_mavjud(dalil, dalil_toliqmas, onto):
    """⭐⭐ Eng muhim test.

    Butun javob bo'ylab yuramiz va HAR BIR iqtibos matnini notes.yaml dagi
    matnlar to'plamiga solishtiramiz. Bittasi ham mos kelmasa — demak
    tizimning biror joyi huquqiy matn TO'QIYAPTI.
    """
    haqiqiy_matnlar = {n.text for n in onto.notes.values()}
    tekshirilgan = 0
    for d in (dalil, dalil_toliqmas):
        for guruh in (d.steps, d.rejections):
            for element in guruh:
                for c in element.citations:
                    assert c.text in haqiqiy_matnlar, (
                        f"'{c.note_id}' iqtibosi notes.yaml da yo'q — "
                        f"matn to'qilgan bo'lishi mumkin"
                    )
                    tekshirilgan += 1
    assert tekshirilgan > 0, "hech qanday iqtibos tekshirilmadi — test bo'sh o'tdi"


def test_bazada_yoq_izoh_xato_koradi(onto):
    """Yo'q izohga murojaat jimgina bo'sh qolmasligi kerak."""
    with pytest.raises(KeyError):
        onto.note("N_MAVJUD_EMAS")


def test_yoq_izoh_jimgina_tashlab_ketilmaydi(onto):
    """⭐ Asos yo'qolishi — kod yo'qolishidan xavfliroq.

    Agar farqlovchi mavjud bo'lmagan izohga ishora qilsa, tizim
    ASOSSIZ javob berib qo'ymasligi kerak. Jimgina o'tkazib yuborilsa,
    foydalanuvchi to'liq ko'rinadigan, lekin asosi kamaygan javob oladi.
    """
    buzuq = onto.model_copy(deep=True)
    d = next(d for d in buzuq.discriminators if d.id == "D_mato")
    d.basis = d.basis + ["N_MAVJUD_EMAS"]

    with pytest.raises(KeyError):
        build_evidence(classify(BLUZKA_TRIKOTAJ, buzuq), buzuq)


def test_yoq_node_izohi_ham_jimgina_tashlab_ketilmaydi(onto):
    buzuq = onto.model_copy(deep=True)
    buzuq.nodes["6106"].note_ids = ["N_MAVJUD_EMAS"]

    with pytest.raises(KeyError):
        build_evidence(classify(BLUZKA_TRIKOTAJ, buzuq), buzuq)


def test_takrorlanuvchi_iqtiboslar_bir_marta_koinadi(dalil):
    for q in dalil.steps:
        idlar = [c.note_id for c in q.citations]
        assert len(idlar) == len(set(idlar))


# --- Halollik: tasdiqlanmagan matn ------------------------------------------


def test_unverified_status_javobda_korinadi(dalil):
    for q in dalil.steps:
        for c in q.citations:
            assert c.status in ("official", "unverified")


def test_tasdiqlanmagan_matn_bayrogi_kotariladi(dalil):
    """Hozircha barcha izohlar unverified — bayroq ko'tarilishi SHART."""
    assert dalil.has_unverified is True
    assert dalil.unverified_note_ids


def test_tasdiqlanmagan_royxat_haqiqiy_iqtiboslarga_mos(dalil, onto):
    for note_id in dalil.unverified_note_ids:
        assert onto.notes[note_id].status == "unverified"


# --- Mato farqlovchisi: loyihaning yuragi -----------------------------------


def test_mato_qadami_trikotaj_tarifiga_ishora_qiladi(dalil):
    q = next(q for q in dalil.steps if q.attribute == "mato_turi")
    assert "N_60_trikotaj_tarif" in {c.note_id for c in q.citations}


def test_6206_rad_etilishi_62_bob_matniga_asoslanadi(dalil):
    r = next(r for r in dalil.rejections if r.code == "62")
    assert "N_62_sarlavha" in {c.note_id for c in r.citations}


def test_har_bir_iqtibos_manba_ishorasiga_ega(dalil):
    """Foydalanuvchi asosni rasmiy manbadan o'zi tekshira olishi kerak."""
    for q in dalil.steps:
        for c in q.citations:
            assert c.ref.strip()
