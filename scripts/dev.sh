#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
scripts/init_db.sh
echo "Starting API on http://127.0.0.1:8000"
echo "Starting Web on http://127.0.0.1:5173"
if [ -x .venv/bin/uvicorn ]; then
  UVICORN=.venv/bin/uvicorn
else
  UVICORN=uvicorn
fi
"$UVICORN" services.api.app.main:app --reload --host 127.0.0.1 --port 8000 &
API_PID=$!
npm --prefix apps/web run dev &
WEB_PID=$!
trap 'kill "$API_PID" "$WEB_PID"' INT TERM EXIT
wait
