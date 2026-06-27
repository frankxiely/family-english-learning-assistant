#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export MOMO_DB_PATH="${MOMO_DB_PATH:-data/sqlite/e2e.db}"
MOMO_API_PORT="${MOMO_API_PORT:-18000}"
PYTHONPATH=. python3 services/api/app/tools/init_db.py --seed-test-data
if [ -x .venv/bin/uvicorn ]; then
  UVICORN=.venv/bin/uvicorn
else
  UVICORN=uvicorn
fi
exec "$UVICORN" services.api.app.main:app --host 127.0.0.1 --port "$MOMO_API_PORT"
