#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
PYTHONPATH=. python3 services/api/app/tools/submit_sample_progress.py
