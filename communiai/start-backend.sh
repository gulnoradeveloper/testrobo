#!/usr/bin/env bash
# CommuniAI backend — Linux/macOS uchun bir martalik ishga tushirish. Talab: Python 3.11+
set -euo pipefail
cd "$(dirname "$0")/backend"
PY=${PYTHON:-python3}
[ -d .venv ] || "$PY" -m venv .venv
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
[ -f .env ] || cp ../.env.example .env
exec python run_local.py
