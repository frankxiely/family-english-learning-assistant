#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export MOMO_API_PORT="${MOMO_API_PORT:-18000}"
export VITE_API_TARGET="${VITE_API_TARGET:-http://127.0.0.1:${MOMO_API_PORT}}"
export VITE_DEV_PORT="${VITE_DEV_PORT:-15173}"
exec npm --prefix apps/web run dev
