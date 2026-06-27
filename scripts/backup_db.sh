#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f data/sqlite/app.db ]; then
  echo "data/sqlite/app.db not found"
  exit 1
fi
stamp="$(date +%Y%m%d_%H%M%S)"
cp data/sqlite/app.db "data/sqlite/backups/app_${stamp}.db"
echo "data/sqlite/backups/app_${stamp}.db"
