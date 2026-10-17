#!/usr/bin/env sh
# Linux / macOS: ./start.sh
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || python3 -m venv .venv || exit 1
[ -f .venv/installed-v2.ok ] || { .venv/bin/python -m pip install -r backend/requirements.txt && touch .venv/installed-v2.ok; } || exit 1
exec .venv/bin/python start.py
