"""Bo‘g‘imTahlil — bitta buyruq bilan ishga tushirish.

    python start.py            (Windows: BOGIMTAHLIL.bat)

1. Python versiyasi va kutubxonalarni tekshiradi (yo‘q bo‘lsa — nima qilishni aytadi).
2. Bo‘sh portni tanlaydi (8765 band bo‘lsa — keyingisi).
3. Serverni ishga tushiradi, u javob bera boshlagach brauzerni ochadi.
Barcha xabarlar logs/server.log fayliga ham yoziladi.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"
REQUIRED = ["fastapi", "uvicorn", "pydantic_settings", "multipart", "sqlalchemy", "alembic", "numpy", "PIL",
            "reportlab", "yaml"]


def say(msg: str = "") -> None:
    print(msg, flush=True)
    try:
        LOGS.mkdir(exist_ok=True)
        with open(LOGS / "server.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def check_python() -> bool:
    if sys.version_info < (3, 10):
        say(f"XATO: Python {sys.version.split()[0]} juda eski. Python 3.11 yoki 3.12 o‘rnating: https://www.python.org/downloads/")
        return False
    return True


def check_packages() -> bool:
    import importlib

    missing = []
    for mod in REQUIRED:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    if missing:
        say(f"XATO: kutubxonalar o‘rnatilmagan: {', '.join(missing)}")
        say(f"Bajaring:  \"{sys.executable}\" -m pip install -r backend/requirements.txt")
        return False
    return True


def free_port(start: int) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                say(f"{port}-port band — keyingisi sinab ko‘rilmoqda")
    raise SystemExit("Bo‘sh port topilmadi")


def open_browser_when_ready(url: str) -> None:
    for _ in range(360):
        try:
            with urllib.request.urlopen(url + "/api/v1/health", timeout=2) as r:
                if r.status == 200:
                    say(f"\nServer tayyor. Brauzerda oching:  {url}\n(Oynani yopmang. To‘xtatish: Ctrl+C)\n")
                    if os.environ.get("BT_NO_BROWSER") != "1":
                        webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.5)
    say("OGOHLANTIRISH: server 3 daqiqada javob bermadi — yuqoridagi xabarlarni o‘qing.")


def main() -> int:
    say("=" * 60)
    say(" Bo‘g‘imTahlil 1.0 — ishga tushirish")
    say(f" Python: {sys.version.split()[0]}  ({sys.executable})")
    say("=" * 60)
    if not (check_python() and check_packages()):
        return 1
    sys.path.insert(0, str(ROOT / "backend"))
    os.chdir(ROOT / "backend")
    port = free_port(int(os.environ.get("BT_PORT", "8765")))
    url = f"http://127.0.0.1:{port}"
    say(f"Manzil: {url}")
    try:
        import torch  # noqa: F401

        say("PyTorch: o‘rnatilgan")
    except Exception:
        say("PyTorch: o‘rnatilmagan — interfeys ishlaydi, sun’iy intellekt tahlili o‘chirilgan "
            "(o‘rnatish: pip install -r backend/requirements-ai.txt)")
    if not Path(os.environ.get("BT_MODEL_PATH", ROOT / "artifacts" / "model.pt")).is_file():
        say("Model: artifacts/model.pt yo‘q — tahlil “model tayyor emas” xabari bilan cheklanadi")

    threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    try:
        import uvicorn

        uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        say(f"XATO: server ishga tushmadi: {type(exc).__name__}: {exc}")
        import traceback

        say(traceback.format_exc())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
