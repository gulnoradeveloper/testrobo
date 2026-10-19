"""Muammo bo‘lsa — barcha holatni bitta faylga yig‘adi: logs/diagnostika.txt

    python diagnostika.py        (Windows: DIAGNOSTIKA.bat)
Faqat standart kutubxona ishlatiladi — kutubxonalar o‘rnatilmagan bo‘lsa ham ishlaydi.
"""
from __future__ import annotations

import importlib
import platform
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"
PACKAGES = ["fastapi", "uvicorn", "pydantic_settings", "multipart", "sqlalchemy", "alembic", "numpy", "PIL",
            "reportlab", "yaml", "torch", "torchvision", "cv2"]


def tail(p: Path, n: int = 30) -> str:
    if not p.is_file():
        return "(fayl yo‘q)"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n:]) or "(bo‘sh)"


def main() -> None:
    out: list[str] = []
    w = out.append
    w(f"Bo‘g‘imTahlil diagnostikasi — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    w(f"Papka: {ROOT}")
    w(f"Python: {sys.version.split()[0]} ({sys.executable})  OS: {platform.platform()}")
    venv = ROOT / ".venv"
    w(f".venv: {'bor' if venv.is_dir() else 'YO‘Q'};  asosiy o‘rnatish belgisi: "
      f"{'bor' if (venv / 'installed-v2.ok').is_file() else 'yo‘q'};  AI o‘rnatish belgisi: "
      f"{'bor' if (venv / 'installed-ai.ok').is_file() else 'yo‘q'}")
    m = ROOT / "artifacts" / "model.pt"
    w(f"Model: {'bor, %.1f MB' % (m.stat().st_size / 2**20) if m.is_file() else 'YO‘Q'} ({m})")
    w("\nKutubxonalar (shu Python’da):")
    for pkg in PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            w(f"  [OK]   {pkg} {getattr(mod, '__version__', '')}")
        except Exception as exc:
            w(f"  [YO‘Q] {pkg} — {type(exc).__name__}")
    w("\nServer holati (portlar 8765–8775):")
    found = False
    for port in range(8765, 8776):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health", timeout=2) as r:
                w(f"  {port}: ishlayapti — {r.read().decode('utf-8', 'replace')[:200]}")
                found = True
        except Exception:
            pass
    if not found:
        w("  Hech qaysi portda server ishlamayapti.")
    for name in ("start.log", "install.log", "ai_install.log", "server.log"):
        w(f"\n===== logs/{name} (oxirgi qatorlar) =====")
        w(tail(LOGS / name))
    LOGS.mkdir(exist_ok=True)
    text = "\n".join(out)
    (LOGS / "diagnostika.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"\nSaqlandi: {LOGS / 'diagnostika.txt'} — shu faylni yuboring.")


if __name__ == "__main__":
    main()
