#!/usr/bin/env sh
# Linux / macOS: ./start.sh
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || python3 -m venv .venv || exit 1
[ -f .venv/installed-v2.ok ] || { .venv/bin/python -m pip install -r backend/requirements.txt && touch .venv/installed-v2.ok; } || exit 1
[ ! -f artifacts/model.pt ] || [ -f .venv/installed-ai.ok ] || { .venv/bin/python -m pip install -r backend/requirements-ai.txt --extra-index-url https://download.pytorch.org/whl/cpu && touch .venv/installed-ai.ok; } || echo "OGOHLANTIRISH: PyTorch o‘rnatilmadi"
exec .venv/bin/python start.py
