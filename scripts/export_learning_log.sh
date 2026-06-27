#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
FORMAT="${1:-markdown}"
PYTHONPATH=. python3 -c "from services.api.app.core import export_learning_log; import json; print(json.dumps(export_learning_log('user_mom', export_format='$FORMAT'), ensure_ascii=False, indent=2))"
