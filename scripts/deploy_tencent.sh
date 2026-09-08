#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  scripts/deploy_tencent.sh [git-ref]

Deploy the current project on a Tencent Cloud Linux server.

Common environment variables:
  WEB_ROOT=/var/www/family-english
  SERVICE_NAME=family-english-api
  HEALTH_URL=http://127.0.0.1:8000/api/health
  PUBLIC_HEALTH_URL=http://175.24.179.41/api/health
  WEB_API_BASE_URL=
  WEB_BASE_PATH=/

Safety switches:
  ALLOW_DIRTY_DEPLOY=1     allow tracked local changes on the server
  INSTALL_PYTHON_DEPS=0    skip python dependency install
  INSTALL_NODE_DEPS=0      skip npm ci
  BUILD_WEB=0              skip frontend build
  RESTART_SERVICE=0        skip systemd restart
  RELOAD_NGINX=1           run nginx -t and reload nginx
  SKIP_HEALTH_CHECK=1      skip curl health checks
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

cd "$(dirname "$0")/.."

TARGET_REF="${1:-${RELEASE_REF:-main}}"
GIT_REMOTE="${GIT_REMOTE:-origin}"

DB_PATH="${MOMO_DB_PATH:-${DB_PATH:-data/sqlite/app.db}}"
BACKUP_DIR="${BACKUP_DIR:-data/sqlite/backups}"
MOMO_DB_PATH="$DB_PATH"
MOMO_AUTO_SEED_TEST_DATA="${MOMO_AUTO_SEED_TEST_DATA:-0}"
if [ "$MOMO_AUTO_SEED_TEST_DATA" != "0" ]; then
  echo "MOMO_AUTO_SEED_TEST_DATA must be 0 for Tencent Cloud deploys" >&2
  exit 1
fi
export MOMO_DB_PATH MOMO_AUTO_SEED_TEST_DATA

if [ -n "${PYTHON_BIN:-}" ]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [ -x .venv/bin/python ]; then
  PYTHON_BIN=.venv/bin/python
else
  PYTHON_BIN=python3
fi
INSTALL_PYTHON_DEPS="${INSTALL_PYTHON_DEPS:-1}"
INSTALL_NODE_DEPS="${INSTALL_NODE_DEPS:-1}"
BUILD_WEB="${BUILD_WEB:-1}"

WEB_ROOT="${WEB_ROOT:-}"
WEB_BASE_PATH="${VITE_BASE_PATH:-${WEB_BASE_PATH:-/}}"
WEB_API_BASE_URL="${VITE_API_BASE_URL:-${WEB_API_BASE_URL:-}}"

SERVICE_NAME="${SERVICE_NAME:-family-english-api}"
RESTART_SERVICE="${RESTART_SERVICE:-1}"
RELOAD_NGINX="${RELOAD_NGINX:-0}"

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/health}"
PUBLIC_HEALTH_URL="${PUBLIC_HEALTH_URL:-}"
SKIP_HEALTH_CHECK="${SKIP_HEALTH_CHECK:-0}"
ALLOW_DIRTY_DEPLOY="${ALLOW_DIRTY_DEPLOY:-0}"

SUDO="${SUDO:-}"
if [ "$(id -u)" != "0" ] && [ -z "$SUDO" ] && command -v sudo >/dev/null 2>&1; then
  SUDO=sudo
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "required command not found: $1" >&2
    exit 1
  fi
}

run_sudo() {
  if [ -n "$SUDO" ]; then
    "$SUDO" "$@"
  else
    "$@"
  fi
}

check_health() {
  url="$1"
  label="$2"
  if [ -z "$url" ]; then
    return 0
  fi
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl not found; skip $label health check"
    return 0
  fi

  tmp="${TMPDIR:-/tmp}/family_english_health_$$.txt"
  i=1
  while [ "$i" -le 30 ]; do
    if curl -fsS "$url" >"$tmp" 2>/dev/null; then
      printf '%s health ok: ' "$label"
      cat "$tmp"
      rm -f "$tmp"
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  rm -f "$tmp"
  echo "$label health check failed: $url" >&2
  return 1
}

require_cmd git
require_cmd "$PYTHON_BIN"

echo "Deploying ref: $TARGET_REF"
echo "Database path: $DB_PATH"
if [ -n "$WEB_ROOT" ]; then
  echo "Web root: $WEB_ROOT"
else
  echo "Web root: not configured; frontend sync will be skipped"
fi
if [ "$RESTART_SERVICE" = "1" ] && [ -n "$SERVICE_NAME" ]; then
  echo "API service: $SERVICE_NAME"
else
  echo "API service restart: skipped"
fi

if [ "$ALLOW_DIRTY_DEPLOY" != "1" ]; then
  dirty="$(git status --porcelain --untracked-files=no)"
  if [ -n "$dirty" ]; then
    echo "tracked local changes found on server; set ALLOW_DIRTY_DEPLOY=1 to override" >&2
    echo "$dirty" >&2
    exit 1
  fi
fi

stamp="$(date +%Y%m%d_%H%M%S)"
safe_ref="$(printf '%s' "$TARGET_REF" | tr '/ :' '___' | tr -cd 'A-Za-z0-9._-')"
if [ -z "$safe_ref" ]; then
  safe_ref=release
fi

mkdir -p "$BACKUP_DIR"
if [ -f "$DB_PATH" ]; then
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(FULL);" >/dev/null
  else
    echo "sqlite3 not found; copying db file and any WAL files without checkpoint"
  fi
  backup_path="$BACKUP_DIR/app-before-${safe_ref}-${stamp}.db"
  cp "$DB_PATH" "$backup_path"
  if [ -f "$DB_PATH-wal" ]; then
    cp "$DB_PATH-wal" "$backup_path-wal"
  fi
  if [ -f "$DB_PATH-shm" ]; then
    cp "$DB_PATH-shm" "$backup_path-shm"
  fi
  echo "Database backup: $backup_path"
else
  echo "Database not found yet; init_db will create it"
fi

git fetch --tags "$GIT_REMOTE"
git checkout "$TARGET_REF"
current_branch="$(git branch --show-current || true)"
if [ "$current_branch" = "$TARGET_REF" ]; then
  git pull --ff-only "$GIT_REMOTE" "$TARGET_REF"
fi

if [ "$INSTALL_PYTHON_DEPS" = "1" ]; then
  "$PYTHON_BIN" -m pip install -e .
fi

PYTHONPATH=. "$PYTHON_BIN" services/api/app/tools/init_db.py

if [ "$BUILD_WEB" = "1" ]; then
  require_cmd npm
  if [ "$INSTALL_NODE_DEPS" = "1" ]; then
    npm --prefix apps/web ci
  fi
  VITE_BASE_PATH="$WEB_BASE_PATH" VITE_API_BASE_URL="$WEB_API_BASE_URL" npm --prefix apps/web run build
fi

if [ -n "$WEB_ROOT" ]; then
  require_cmd rsync
  if [ ! -d apps/web/dist ]; then
    echo "apps/web/dist not found; set BUILD_WEB=1 or build before syncing" >&2
    exit 1
  fi
  run_sudo mkdir -p "$WEB_ROOT"
  run_sudo rsync -a --delete apps/web/dist/ "$WEB_ROOT"/
  echo "Frontend synced to $WEB_ROOT"
fi

if [ "$RESTART_SERVICE" = "1" ] && [ -n "$SERVICE_NAME" ]; then
  require_cmd systemctl
  run_sudo systemctl restart "$SERVICE_NAME"
  echo "Restarted $SERVICE_NAME"
fi

if [ "$RELOAD_NGINX" = "1" ]; then
  run_sudo nginx -t
  run_sudo systemctl reload nginx
  echo "Reloaded nginx"
fi

if [ "$SKIP_HEALTH_CHECK" != "1" ]; then
  check_health "$HEALTH_URL" "local API"
  check_health "$PUBLIC_HEALTH_URL" "public API"
fi

echo "Deploy finished: $TARGET_REF"
