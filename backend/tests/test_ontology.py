"""1-bosqich: Ontologiya yaxlitligi.

Bu testlar ma'lumotning o'zini tekshiradi. Ontologiya — tizimning huquqiy
poydevori: agar u buzuq bo'lsa, undan yuqoridagi hech narsaga ishonib
bo'lmaydi. Shuning uchun bu yerda mantiq emas, INVARIANTLAR sinaladi.
"""

import pytest

from app.ontology import load_ontology

FINAL_KOD_UZUNLIGI = 10  # raqamlar soni, probellarsiz


@pytest.fixture(scope="module")
def onto():
    return load_ontology()


# --- Daraxt strukturasi -----------------------------------------------------


def test_ildiz_mavjud_va_parenti_yoq(onto):
    ildiz = onto.nodes[onto.root]
    assert ildiz.parent is None


def test_har_bir_node_parenti_mavjud(onto):
    for kod, node in onto.nodes.items():
        if kod == onto.root:
            continue
        assert node.parent is not None, f"{kod}: parent ko'rsatilmagan"
        assert node.parent in onto.nodes, f"{kod}: parent '{node.parent}' mavjud emas"


def test_daraxtda_sikl_yoq(onto):
    for kod in onto.nodes:
        korilgan = set()
        joriy = kod
        while joriy is not None:
            assert joriy not in korilgan, f"sikl aniqlandi: {kod} -> ... -> {joriy}"
            korilgan.add(joriy)
            joriy = onto.nodes[joriy].parent


def test_har_bir_node_ildizdan_yetib_boriladi(onto):
    for kod in onto.nodes:
        joriy = kod
        while onto.nodes[joriy].parent is not None:
            joriy = onto.nodes[joriy].parent
        assert joriy == onto.root, f"{kod} ildizga ulanmagan"


def test_yakuniy_bolmagan_node_boshi_berk_emas(onto):
    """Har bir yakuniy bo'lmagan tugunda kamida bitta farqlovchi bo'lishi shart.

    Aks holda dvigatel u yerga borib qotib qoladi va foydalanuvchiga
    na kod, na savol bera oladi.
    """
    for kod, node in onto.nodes.items():
        if node.is_final:
            continue
        assert onto.discriminators_at(kod), f"{kod}: farqlovchi yo'q, lekin yakuniy ham emas"


def test_yakuniy_node_farqlovchiga_ega_emas(onto):
    for kod, node in onto.nodes.items():
        if node.is_final:
            assert not onto.discriminators_at(kod), f"{kod}: yakuniy, lekin farqlovchisi bor"


# --- Kodlar -----------------------------------------------------------------


def test_har_bir_yaproq_10_xonali_kod(onto):
    for kod, node in onto.nodes.items():
        if not node.is_final:
            continue
        raqamlar = kod.replace(" ", "")
        assert raqamlar.isdigit(), f"{kod}: kod faqat raqamlardan iborat bo'lishi kerak"
        assert len(raqamlar) == FINAL_KOD_UZUNLIGI, (
            f"{kod}: yakuniy kod {FINAL_KOD_UZUNLIGI} xonali bo'lishi shart, "
            f"{len(raqamlar)} ta topildi"
        )


def test_yakuniy_node_boj_stavkasiga_ega(onto):
    for kod, node in onto.nodes.items():
        if node.is_final:
            assert node.duty_rate is not None, f"{kod}: boj stavkasi ko'rsatilmagan"


# --- Farqlovchilar ----------------------------------------------------------


def test_farqlovchi_idlari_unikal(onto):
    idlar = [d.id for d in onto.discriminators]
    assert len(idlar) == len(set(idlar))


def test_farqlovchi_at_node_mavjud(onto):
    for d in onto.discriminators:
        assert d.at_node in onto.nodes, f"{d.id}: at_node '{d.at_node}' mavjud emas"


def test_farqlovchi_targetlari_mavjud_nodega_ishora_qiladi(onto):
    for d in onto.discriminators:
        for qiymat, target in d.branches.items():
            assert target in onto.nodes, f"{d.id}[{qiymat}]: target '{target}' mavjud emas"


def test_farqlovchi_targetlari_bevosita_farzand(onto):
    """Tarmoq faqat bir pog'ona pastga tusha oladi — daraxt yaxlitligi uchun."""
    for d in onto.discriminators:
        for qiymat, target in d.branches.items():
            assert onto.nodes[target].parent == d.at_node, (
                f"{d.id}[{qiymat}]: '{target}' ning parenti '{d.at_node}' emas"
            )


def test_farqlovchi_kamida_ikki_tarmoqqa_ega(onto):
    for d in onto.discriminators:
        assert len(d.branches) >= 2, f"{d.id}: bitta tarmoqli farqlovchi ma'nosiz"


def test_bitta_nodeda_bitta_atribut_ikki_marta_ishlatilmaydi(onto):
    korilgan = set()
    for d in onto.discriminators:
        kalit = (d.at_node, d.attribute)
        assert kalit not in korilgan, f"{d.at_node}: '{d.attribute}' takrorlangan"
        korilgan.add(kalit)


# --- Atributlar -------------------------------------------------------------


def test_farqlovchi_atributi_elon_qilingan(onto):
    for d in onto.discriminators:
        assert d.attribute in onto.attributes, f"{d.id}: '{d.attribute}' atributi e'lon qilinmagan"


def test_atribut_qiymatlari_yopiq_royxat(onto):
    """Tarmoq kaliti atributning e'lon qilingan qiymatlaridan biri bo'lishi shart.

    Bu ekstraktor uchun ham muhim: model erkin matn qaytara olmaydi.
    """
    for d in onto.discriminators:
        ruxsat = set(onto.attributes[d.attribute].values)
        for qiymat in d.branches:
            assert qiymat in ruxsat, (
                f"{d.id}: '{qiymat}' qiymati '{d.attribute}' atributida e'lon qilinmagan. "
                f"Ruxsat etilgan: {sorted(ruxsat)}"
            )


def test_har_bir_atribut_ozbekcha_savolga_ega(onto):
    """Atribut noma'lum bo'lganda foydalanuvchidan nima so'rashni bilishimiz kerak."""
    for nom, atr in onto.attributes.items():
        assert atr.question_uz.strip(), f"{nom}: savol matni bo'sh"
        assert atr.values, f"{nom}: qiymatlar ro'yxati bo'sh"


# --- Huquqiy asos -----------------------------------------------------------


def test_har_bir_farqlovchi_legal_basisga_ega(onto):
    """Asossiz farqlovchi bo'lishi mumkin emas — tizimning butun qiymati shunda."""
    for d in onto.discriminators:
        assert d.basis, f"{d.id}: huquqiy asos ko'rsatilmagan"
        for note_id in d.basis:
            assert note_id in onto.notes, f"{d.id}: '{note_id}' izohi mavjud emas"


def test_har_bir_node_status_maydoniga_ega(onto):
    """Kodlar va boj stavkalari ham tasdiqlanishi kerak, faqat izohlar emas."""
    for kod, node in onto.nodes.items():
        assert node.status in ("official", "unverified"), (
            f"{kod}: status '{node.status}' noto'g'ri"
        )


def test_har_bir_izoh_status_maydoniga_ega(onto):
    for note_id, note in onto.notes.items():
        assert note.status in ("official", "unverified"), (
            f"{note_id}: status '{note.status}' — 'official' yoki 'unverified' bo'lishi kerak"
        )


def test_har_bir_izoh_manba_ishorasiga_ega(onto):
    """Foydalanuvchi asosni o'zi tekshira olishi uchun manba aniq bo'lishi shart."""
    for note_id, note in onto.notes.items():
        assert note.ref.strip(), f"{note_id}: manba ishorasi (ref) bo'sh"
        assert note.text.strip(), f"{note_id}: izoh matni bo'sh"


def test_yetim_izoh_yoq(onto):
    """Hech qayerda ishlatilmaydigan izoh — bu ma'lumot chirishi belgisi."""
    ishlatilgan = set()
    for d in onto.discriminators:
        ishlatilgan.update(d.basis)
    for node in onto.nodes.values():
        ishlatilgan.update(node.note_ids)
    yetim = set(onto.notes) - ishlatilgan
    assert not yetim, f"ishlatilmagan izohlar: {sorted(yetim)}"


def test_node_izohlari_mavjud(onto):
    for kod, node in onto.nodes.items():
        for note_id in node.note_ids:
            assert note_id in onto.notes, f"{kod}: '{note_id}' izohi mavjud emas"


# --- Qamrov: foydalanuvchi misoli -------------------------------------------


def test_bluzka_misoli_ontologiyada_mavjud(onto):
    """Loyihaning asosiy misoli: 6106 (trikotaj) va 6206 (to'qima)."""
    assert "6106 10 000 0" in onto.nodes
    assert "6206 30 000 0" in onto.nodes


def test_61_va_62_bir_xil_farqlovchi_ostida(onto):
    """Aynan shu farqlovchi loyihaning mavjudlik sababi."""
    mos = [
        d
        for d in onto.discriminators
        if "61" in d.branches.values() and "62" in d.branches.values()
    ]
    assert len(mos) == 1, "61 va 62 ni ajratuvchi aynan bitta farqlovchi bo'lishi kerak"
    assert mos[0].attribute == "mato_turi"


def test_8471_va_8517_ontologiyada_mavjud(onto):
    """Ikkinchi qamrov: 84/85 boblar."""
    assert any(k.startswith("8471") for k in onto.nodes)
    assert any(k.startswith("8517") for k in onto.nodes)
