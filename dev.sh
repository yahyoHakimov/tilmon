#!/usr/bin/env bash
#
# Tilmon — backend va frontendni birga ishga tushiradi.
#
#   ./dev.sh                        odatiy portlar (8000 / 5173)
#   BACKEND_PORT=9000 ./dev.sh      boshqa port
#
# Ctrl+C ikkala jarayonni ham (va ularning bolalarini) to'xtatadi.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

if [ -t 1 ]; then
  DIM=$'\033[2m'; BOLD=$'\033[1m'; RED=$'\033[31m'; GRN=$'\033[32m'
  YEL=$'\033[33m'; BLU=$'\033[34m'; OFF=$'\033[0m'
else
  DIM=''; BOLD=''; RED=''; GRN=''; YEL=''; BLU=''; OFF=''
fi

xato()  { printf '%s\n' "${RED}✗ $*${OFF}" >&2; exit 1; }
ogoh()  { printf '%s\n' "${YEL}⚠ $*${OFF}"; }
xabar() { printf '%s\n' "${DIM}· $*${OFF}"; }

# --- Tekshiruvlar ----------------------------------------------------------

command -v uv  >/dev/null 2>&1 || xato "uv topilmadi. O'rnatish: https://docs.astral.sh/uv/"
command -v npm >/dev/null 2>&1 || xato "npm topilmadi. Node.js o'rnating."

band_mi() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -q ":$1 "
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    return 1  # tekshira olmasak, to'sqinlik qilmaymiz
  fi
}

band_mi "$BACKEND_PORT"  && xato "$BACKEND_PORT porti band. Boshqa port: BACKEND_PORT=… ./dev.sh"
band_mi "$FRONTEND_PORT" && xato "$FRONTEND_PORT porti band. Boshqa port: FRONTEND_PORT=… ./dev.sh"

# --- Bog'liqliklar ---------------------------------------------------------

xabar "backend bog'liqliklari tekshirilmoqda…"
(cd "$ROOT/backend" && uv sync --quiet)

# --- Ma'lumotlar bazasi ----------------------------------------------------
#
# Auth uchun Postgres kerak. Lokal ishlab chiqishda alohida Docker
# konteyneri ishlatiladi — bu tizimdagi boshqa bazalarga tegmaydi.
# Serverda esa oddiy `systemd` postgres bo'ladi (DATABASE_URL orqali).

PG_KONTEYNER="tilmon-pg-dev"
PG_PORT=55432

if [ -z "${DATABASE_URL:-}" ] && [ ! -f "$ROOT/backend/.env" ]; then
  if command -v docker >/dev/null 2>&1; then
    if ! docker ps --format '{{.Names}}' | grep -qx "$PG_KONTEYNER"; then
      if docker ps -a --format '{{.Names}}' | grep -qx "$PG_KONTEYNER"; then
        xabar "Postgres konteyneri ishga tushirilmoqda…"
        docker start "$PG_KONTEYNER" >/dev/null
      else
        xabar "Postgres konteyneri yaratilmoqda (birinchi marta)…"
        docker run -d --name "$PG_KONTEYNER" \
          -e POSTGRES_USER=tilmon -e POSTGRES_PASSWORD=tilmon_dev \
          -e POSTGRES_DB=tilmon -p "$PG_PORT:5432" \
          postgres:18-alpine >/dev/null
      fi
      for _ in $(seq 1 60); do
        docker exec "$PG_KONTEYNER" pg_isready -U tilmon >/dev/null 2>&1 && break
        sleep 0.5
      done
    fi
    export DATABASE_URL="postgresql+psycopg://tilmon:tilmon_dev@127.0.0.1:$PG_PORT/tilmon"
  else
    ogoh "Docker ham, backend/.env ham yo'q — Postgres topilmadi."
    ogoh "  Kirish va ro'yxatdan o'tish ishlamaydi."
    ogoh "  DATABASE_URL ni o'rnating yoki Docker o'rnating."
    echo
  fi
fi

if [ -n "${DATABASE_URL:-}" ] || [ -f "$ROOT/backend/.env" ]; then
  xabar "migratsiyalar qo'llanmoqda…"
  if ! (cd "$ROOT/backend" && uv run alembic upgrade head >/dev/null 2>&1); then
    ogoh "Migratsiyalarni qo'llab bo'lmadi — bazaga ulanishni tekshiring."
    echo
  fi
fi

# Lokal HTTP uchun: `Secure` cookie HTTP so'rovlarda yuborilmaydi,
# ya'ni kirish ishlamay qoladi. Ishlab chiqarishda bu 1 bo'lishi shart.
export SECURE_COOKIES="${SECURE_COOKIES:-0}"

if [ ! -d "$ROOT/web/node_modules" ]; then
  xabar "frontend bog'liqliklari o'rnatilmoqda (birinchi marta, biroz vaqt oladi)…"
  (cd "$ROOT/web" && npm install --silent)
fi

# --- OPENAI_API_KEY --------------------------------------------------------
#
# Kalitsiz tizim yiqilmaydi: model chaqiruvi xato beradi va tasnif
# "ma'lumot yetarli emas" holatiga tushadi — bu loyihaning ataylab
# tanlangan xatti-harakati. Lekin erkin matn tahlil qilinmaydi,
# shuning uchun buni ochiq aytish kerak.

if [ ! -f "$ROOT/backend/.env" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  ogoh "OPENAI_API_KEY topilmadi (backend/.env yo'q)."
  ogoh "  Tizim ishlaydi, lekin erkin matnni tahlil qila olmaydi —"
  ogoh "  har bir so'rov 'ma'lumot yetarli emas' javobini beradi."
  ogoh "  Javob tugmalari orqali qo'lda tasnif qilish baribir ishlaydi."
  ogoh "  Sozlash:  cp backend/.env.example backend/.env"
  echo
fi

# --- Jarayonlarni boshqarish ----------------------------------------------
#
# Muhim tafsilot: xizmatlar `| prefiks` quvuri orqali ishga tushiriladi,
# shuning uchun `$!` quvurning OXIRGI jarayonini (prefiks) beradi, xizmatni
# emas. Uni o'ldirish uvicorn/vite ni to'xtatmaydi.
#
# Yechim: subshell `exec` dan OLDIN o'z PID ini faylga yozadi. `exec`
# jarayon obrazini almashtiradi, PID esa o'zgarmaydi — ya'ni fayldagi
# raqam aynan xizmatning PID i bo'ladi.

PIDDIR="$(mktemp -d)"
QUVUR_PIDS=()

oldir_daraxt() {
  # Jarayonni bolalari bilan birga to'xtatadi.
  # uvicorn --reload reloader + worker, uv esa python bolasini yaratadi —
  # shuning uchun butun daraxtni aylanib chiqish kerak.
  local pid="$1" sig="${2:-TERM}" bola
  for bola in $(pgrep -P "$pid" 2>/dev/null || true); do
    oldir_daraxt "$bola" "$sig"
  done
  kill -"$sig" "$pid" 2>/dev/null || true
}

tozala() {
  trap - INT TERM EXIT
  echo
  xabar "to'xtatilmoqda…"

  for f in "$PIDDIR"/*.pid; do
    [ -f "$f" ] || continue
    oldir_daraxt "$(cat "$f")" TERM
  done

  # Yumshoq to'xtash uchun vaqt beramiz.
  for _ in $(seq 1 30); do
    local tirik=0
    for f in "$PIDDIR"/*.pid; do
      [ -f "$f" ] || continue
      kill -0 "$(cat "$f")" 2>/dev/null && tirik=1
    done
    [ "$tirik" -eq 0 ] && break
    sleep 0.1
  done

  # Qolganini majburan.
  for f in "$PIDDIR"/*.pid; do
    [ -f "$f" ] || continue
    oldir_daraxt "$(cat "$f")" KILL
  done

  for pid in "${QUVUR_PIDS[@]:-}"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done

  wait 2>/dev/null || true
  rm -rf "$PIDDIR"
  printf '%s\n' "${DIM}· to'xtatildi${OFF}"
}
trap tozala INT TERM EXIT

prefiks() {
  # Har bir satrni yorliq bilan belgilaydi — qaysi tomondan kelgani
  # darhol ko'rinsin.
  local yorliq="$1"
  while IFS= read -r satr; do
    printf '%s %s\n' "$yorliq" "$satr"
  done
}

# --- Ishga tushirish -------------------------------------------------------

printf '%s\n' "${BOLD}Tilmon${OFF} ${DIM}— ishga tushmoqda${OFF}"
echo

(
  cd "$ROOT/backend"
  echo $BASHPID > "$PIDDIR/backend.pid"
  exec uv run uvicorn app.api:app \
    --host 127.0.0.1 --port "$BACKEND_PORT" --reload 2>&1
) | prefiks "${BLU}[backend ]${OFF}" &
QUVUR_PIDS+=($!)

(
  cd "$ROOT/web"
  echo $BASHPID > "$PIDDIR/frontend.pid"
  export BACKEND_URL="http://127.0.0.1:$BACKEND_PORT"
  export FRONTEND_PORT
  exec npx vite --port "$FRONTEND_PORT" 2>&1
) | prefiks "${GRN}[frontend]${OFF}" &
QUVUR_PIDS+=($!)

# Backend ko'tarilishini kutamiz — havolalarni erta ko'rsatmaslik uchun.
for _ in $(seq 1 60); do
  curl -sf "http://127.0.0.1:$BACKEND_PORT/api/healthz" >/dev/null 2>&1 && break
  sleep 0.5
done

echo
printf '%s\n' "  ${BOLD}Ilova${OFF}      http://localhost:$FRONTEND_PORT"
printf '%s\n' "  ${DIM}API${OFF}        http://127.0.0.1:$BACKEND_PORT/api/healthz"
printf '%s\n' "  ${DIM}Hujjatlar${OFF}  http://127.0.0.1:$BACKEND_PORT/docs"
echo
printf '%s\n' "  ${DIM}To'xtatish: Ctrl+C${OFF}"
echo

wait
