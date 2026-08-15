"""9-bosqich (1-qism): Parol xeshlash.

Bu modulda bitta qoida: PAROLNI QAYTARIB BO'LMASLIGI KERAK.

Ma'lumot bazasi o'g'irlansa ham, undagi yozuvlardan parollarni tiklab
bo'lmasligi shart. Shuning uchun argon2id — hozirgi tavsiya etilgan
algoritm (Password Hashing Competition g'olibi), sekin va xotira talab
qiladigan, ya'ni GPU bilan brute-force qilish qimmat.

Parol siyosati ham shu yerda: qisqa yoki juda oddiy parol qabul
qilinmaydi. Bu bezak emas — foydalanuvchining bojxona deklaratsiyasiga
ta'sir qiladigan tizimga kirishi himoyalanishi kerak.
"""

import pytest

from app.security import (
    MIN_PAROL_UZUNLIGI,
    ParolZaif,
    hash_password,
    tekshir_parol_kuchi,
    verify_password,
)

YAXSHI_PAROL = "Bluzka-6106-trikotaj"


# --- Xeshlash ---------------------------------------------------------------


def test_xesh_parolni_oz_ichiga_olmaydi():
    """⭐ Eng asosiy tekshiruv."""
    xesh = hash_password(YAXSHI_PAROL)
    assert YAXSHI_PAROL not in xesh
    assert YAXSHI_PAROL.lower() not in xesh.lower()


def test_xesh_argon2id_formatida():
    assert hash_password(YAXSHI_PAROL).startswith("$argon2id$")


def test_bir_xil_parol_har_safar_boshqa_xesh_beradi():
    """Tuz (salt) tasodifiy — bir xil parolli ikki foydalanuvchi bazada
    bir xil ko'rinmasligi kerak."""
    assert hash_password(YAXSHI_PAROL) != hash_password(YAXSHI_PAROL)


def test_togri_parol_tasdiqlanadi():
    assert verify_password(hash_password(YAXSHI_PAROL), YAXSHI_PAROL) is True


def test_notogri_parol_rad_etiladi():
    assert verify_password(hash_password(YAXSHI_PAROL), "boshqa-parol-123") is False


def test_registr_muhim():
    assert verify_password(hash_password(YAXSHI_PAROL), YAXSHI_PAROL.lower()) is False


def test_buzuq_xesh_xato_kotarmaydi():
    """Bazadagi buzuq yozuv 500 xatosiga olib kelmasligi kerak."""
    assert verify_password("bu xesh emas", YAXSHI_PAROL) is False
    assert verify_password("", YAXSHI_PAROL) is False


def test_bosh_parol_tasdiqlanmaydi():
    assert verify_password(hash_password(YAXSHI_PAROL), "") is False


def test_uzun_parol_qabul_qilinadi():
    """Argon2 uzunlik chegarasi qo'ymaydi — bcrypt dagi 72 bayt
    muammosi bu yerda yo'q."""
    uzun = "a" * 500 + "Z9!"
    assert verify_password(hash_password(uzun), uzun) is True


# --- Parol siyosati ---------------------------------------------------------


def test_yaxshi_parol_qabul_qilinadi():
    tekshir_parol_kuchi(YAXSHI_PAROL)  # xato ko'tarmasligi kerak


def test_qisqa_parol_rad_etiladi():
    with pytest.raises(ParolZaif):
        tekshir_parol_kuchi("Qisqa1!")


def test_minimal_uzunlik_kamida_10():
    """Chegara tasodifiy tanlanmagan: 8 belgi hozirgi apparatda tez
    sindiriladi."""
    assert MIN_PAROL_UZUNLIGI >= 10


def test_faqat_raqamdan_iborat_parol_rad_etiladi():
    with pytest.raises(ParolZaif):
        tekshir_parol_kuchi("12345678901234")


def test_juda_ommabop_parol_rad_etiladi():
    for p in ("parol12345", "password123", "qwerty123456", "1234567890"):
        with pytest.raises(ParolZaif):
            tekshir_parol_kuchi(p)


def test_email_ga_oxshash_parol_rad_etiladi():
    """Foydalanuvchilar ko'pincha emailini parol qilib qo'yadi."""
    with pytest.raises(ParolZaif):
        tekshir_parol_kuchi("sokhib@jett.uz", email="sokhib@jett.uz")


def test_email_qismini_parol_qilish_rad_etiladi():
    with pytest.raises(ParolZaif):
        tekshir_parol_kuchi("sokhib-sokhib", email="sokhib@jett.uz")


def test_xato_matni_ozbekcha_va_tushunarli():
    with pytest.raises(ParolZaif) as e:
        tekshir_parol_kuchi("qisqa")
    assert str(MIN_PAROL_UZUNLIGI) in str(e.value)


# --- Vaqt hujumiga qarshi ---------------------------------------------------


def test_mavjud_bolmagan_foydalanuvchi_uchun_soxta_xesh_bor():
    """⭐ Email mavjudligini vaqt bo'yicha aniqlab bo'lmasligi kerak.

    Agar foydalanuvchi topilmaganda darhol False qaytarsak, javob vaqti
    mavjud foydalanuvchinikidan sezilarli qisqa bo'ladi va hujumchi
    shu orqali qaysi emaillar ro'yxatdan o'tganini aniqlaydi.

    Yechim: topilmagan holatda ham soxta xeshni tekshirib chiqamiz.
    """
    from app.security import SOXTA_XESH

    assert SOXTA_XESH.startswith("$argon2id$")
    assert verify_password(SOXTA_XESH, "har qanday parol") is False
