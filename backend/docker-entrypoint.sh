#!/usr/bin/env sh
# Konteyner ishga tushganda migratsiyalarni qo'llaydi, so'ng CMD ni ishga tushiradi.
# Baza `db` servisi tayyor bo'lguncha kutamiz (compose depends_on healthcheck
# odatda yetarli, lekin qo'shimcha himoya sifatida qayta urinamiz).
set -e

echo "[entrypoint] migratsiyalar qo'llanmoqda…"
n=0
until .venv/bin/alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 10 ]; then
    echo "[entrypoint] migratsiya 10 urinishdan keyin ham bajarilmadi — chiqilmoqda." >&2
    exit 1
  fi
  echo "[entrypoint] baza hali tayyor emas, 2s dan keyin qayta urinamiz ($n/10)…"
  sleep 2
done

echo "[entrypoint] ishga tushirilmoqda: $*"
exec "$@"
