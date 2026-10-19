"""Bo‘g‘imTahlil — bitta buyruq bilan ishga tushirish.

    python start.py            (Windows: BOGIMTAHLIL.bat)

1. Python versiyasi va kutubxonalarni tekshiradi.
2. Bo‘sh portni tanlaydi (8765 band bo‘lsa — keyingisi).
3. Serverni alohida jarayonda ishga tushiradi; uning barcha xabarlari logs/server.log ga yoziladi
   (konsolga emas — Windows konsolida sichqoncha bilan bosish serverni “muzlatib” qo‘ymaydi).
4. Server javob bera boshlagach brauzerni ochadi.
5. Server kutilmaganda to‘xtasa — sababini ko‘rsatadi va qayta ishga tushiradi.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"
SERVER_LOG = LOGS / "server.log"
REQUIRED = ["fastapi", "uvicorn", "pydantic_settings", "multipart", "sqlalchemy", "alembic", "numpy", "PIL",
            "reportlab", "yaml"]
MAX_RESTARTS = 3


def say(msg: str = "") -> None:
    print(msg, flush=True)
    try:
        LOGS.mkdir(exist_ok=True)
        with open(LOGS / "start.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def disable_windows_quickedit() -> None:
    """Windows konsolida “QuickEdit” rejimi oynaga bosilganda dasturni to‘xtatib qo‘yadi — o‘chiramiz."""
    if os.name != "nt":
        return
    try:
        import ctypes

        k = ctypes.windll.kernel32
        handle = k.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_uint32()
        if k.GetConsoleMode(handle, ctypes.byref(mode)):
            k.SetConsoleMode(handle, (mode.value & ~0x0040) | 0x0080)  # QUICK_EDIT o‘chiriladi
    except Exception:
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


def healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/api/v1/health", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def tail(path: Path, n: int = 25) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:])
    except OSError:
        return "(log fayli o‘qilmadi)"


def start_server(port: int) -> subprocess.Popen:
    LOGS.mkdir(exist_ok=True)
    log = open(SERVER_LOG, "a", encoding="utf-8")
    log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} server ishga tushirilmoqda (port {port}) =====\n")
    log.flush()
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port),
           "--log-level", "info"]
    return subprocess.Popen(cmd, cwd=ROOT / "backend", stdout=log, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, env=env)


def main() -> int:
    disable_windows_quickedit()
    say("=" * 64)
    say(" Bo‘g‘imTahlil 1.0 — ishga tushirish")
    say(f" Python: {sys.version.split()[0]}  ({sys.executable})")
    say("=" * 64)
    if not (check_python() and check_packages()):
        return 1
    say(f"Dastur papkasi: {ROOT}")
    model_path = Path(os.environ.get("BT_MODEL_PATH", ROOT / "artifacts" / "model.pt"))
    if model_path.is_file():
        say(f"Model fayli: {model_path} ({model_path.stat().st_size / 2**20:.1f} MB)")
    else:
        say(f"Model fayli: YO‘Q ({model_path}) — tahlil cheklangan bo‘ladi")
    want = int(os.environ.get("BT_PORT", "8765"))
    if healthy(f"http://127.0.0.1:{want}"):
        say(f"\nDIQQAT: http://127.0.0.1:{want} da Bo‘g‘imTahlilning BOSHQA (eski) nusxasi ishlayapti.")
        say("Eski qora oynani yoping — aks holda brauzerda eski versiya ochilishi mumkin.")
        say("Bu nusxa boshqa portda ishga tushiriladi va brauzer to‘g‘ri manzilni o‘zi ochadi.\n")
    port = free_port(want)
    url = f"http://127.0.0.1:{port}"
    try:
        import torch  # noqa: F401

        say("PyTorch: o‘rnatilgan")
    except Exception:
        say("PyTorch: o‘rnatilmagan — interfeys ishlaydi, sun’iy intellekt tahlili o‘chirilgan")

    restarts, opened = 0, False
    proc = start_server(port)
    try:
        while True:
            # Server tayyor bo‘lishini kutish
            for _ in range(360):
                if proc.poll() is not None or healthy(url):
                    break
                time.sleep(0.5)
            if proc.poll() is None and healthy(url):
                say(f"\nServer ishlayapti:  {url}")
                say("Bu oynani YOPMANG — dastur shu oynada ishlaydi. To‘xtatish: Ctrl+C.")
                say(f"Server xabarlari: {SERVER_LOG}\n")
                if not opened and os.environ.get("BT_NO_BROWSER") != "1":
                    webbrowser.open(url)
                opened = True
                code = proc.wait()
            else:
                code = proc.poll()
                if code is None:  # 3 daqiqada javob bermadi
                    say("XATO: server 3 daqiqada javob bermadi. Oxirgi xabarlar:\n" + tail(SERVER_LOG))
                    proc.terminate()
                    return 1
            say(f"\nXATO: server to‘xtadi (kod {code}). Oxirgi xabarlar ({SERVER_LOG}):\n" + tail(SERVER_LOG))
            restarts += 1
            if restarts > MAX_RESTARTS:
                say("Server bir necha marta to‘xtadi — logs\\server.log faylini yuboring.")
                return 1
            say(f"Server qayta ishga tushirilmoqda ({restarts}/{MAX_RESTARTS})...")
            time.sleep(2)
            proc = start_server(port)
    except KeyboardInterrupt:
        say("\nTo‘xtatilmoqda...")
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        return 0


if __name__ == "__main__":
    sys.exit(main())
