"""Test uchun umumiy fixture'lar.

Muhim tamoyil: tizim YADROSI bazasiz test qilinadi. Ontologiya, dvigatel,
asos zanjiri va ekstraktor testlari hech qanday infratuzilma talab
qilmaydi — ular `pytest` ni har qanday muhitda ishlatib bo'ladi.

Faqat auth va foydalanuvchi bilan bog'liq testlar Postgres talab qiladi.
Ular `@pytest.mark.db` bilan belgilanadi va baza yo'q bo'lsa aniq
sabab bilan o'tkazib yuboriladi.
"""

from __future__ import annotations

import os

# Testlar HTTP orqali ishlaydi (TestClient -> http://testserver).
# `Secure` bayrog'i qo'yilgan cookie HTTP so'rovlarda YUBORILMAYDI —
# shuning uchun testlarda u o'chiriladi. Ishlab chiqarishda esa
# `SECURE_COOKIES=1` bo'lishi shart: buni `test_secure_cookie_sozlamasi`
# tekshiradi.
#
# Bu sozlamalar `app.config` import qilinishidan OLDIN qo'yilishi kerak.
os.environ.setdefault("SECURE_COOKIES", "0")
os.environ.setdefault("SESSION_SECRET", "test-uchun-sir-" + "x" * 32)

import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session as SASession  # noqa: E402

from app.db import Base  # noqa: E402

VARSAYILGAN_TEST_URL = (
    "postgresql+psycopg://tilmon:tilmon_dev@127.0.0.1:55432/tilmon_test"
)


def _test_url() -> str:
    return os.getenv("TILMON_TEST_DATABASE_URL", VARSAYILGAN_TEST_URL)


def _baza_yaratilgan(url: str) -> None:
    """Test bazasi yo'q bo'lsa yaratadi."""
    admin_url, _, baza = url.rpartition("/")
    admin = create_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        bor = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": baza}
        ).scalar()
        if not bor:
            conn.execute(text(f'CREATE DATABASE "{baza}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    url = _test_url()
    try:
        _baza_yaratilgan(url)
        e = create_engine(url)
        with e.connect():
            pass
    except Exception as xato:  # noqa: BLE001
        pytest.skip(
            f"Postgres mavjud emas ({type(xato).__name__}). "
            f"Ishga tushirish:\n"
            f"  docker run -d --name tilmon-pg-dev "
            f"-e POSTGRES_USER=tilmon -e POSTGRES_PASSWORD=tilmon_dev "
            f"-e POSTGRES_DB=tilmon -p 55432:5432 postgres:18-alpine\n"
            f"Yoki TILMON_TEST_DATABASE_URL ni o'rnating.",
            allow_module_level=True,
        )

    Base.metadata.drop_all(e)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)
    e.dispose()


@pytest.fixture
def db(engine):
    """Har bir test o'z tranzaksiyasida ishlaydi va oxirida bekor qilinadi.

    Shunda testlar bir-birining ma'lumotini ko'rmaydi va tartibga
    bog'liq bo'lmaydi.
    """
    conn = engine.connect()
    trans = conn.begin()
    sess = SASession(bind=conn)
    try:
        yield sess
    finally:
        sess.close()
        # IntegrityError kutayotgan testlarda tranzaksiya allaqachon
        # bekor qilingan bo'ladi — qayta bekor qilish ogohlantirish beradi.
        if trans.is_active:
            trans.rollback()
        conn.close()
