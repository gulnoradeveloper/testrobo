"""Muhitni tekshirish: Python versiyasi, kutubxonalar, model va dataset holati.

    python ai/scripts/check_env.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = [
    ("numpy", "numpy"), ("pandas", "pandas"), ("PIL", "pillow"), ("cv2", "opencv-python-headless"),
    ("sklearn", "scikit-learn"), ("matplotlib", "matplotlib"), ("yaml", "pyyaml"), ("torch", "torch"),
    ("torchvision", "torchvision"), ("fastapi", "fastapi"), ("uvicorn", "uvicorn"), ("sqlalchemy", "sqlalchemy"),
    ("alembic", "alembic"), ("reportlab", "reportlab"), ("multipart", "python-multipart"),
    ("pydantic_settings", "pydantic-settings"),
]


def main() -> int:
    ok = True
    v = sys.version_info
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if v < (3, 10):
        print("  XATO: Python 3.10 yoki yangiroq kerak (3.11 / 3.12 tavsiya etiladi)")
        ok = False
    missing = []
    for mod, pkg in PACKAGES:
        try:
            m = importlib.import_module(mod)
            print(f"  [OK]   {pkg} {getattr(m, '__version__', '')}")
        except Exception:
            print(f"  [YO‘Q] {pkg}")
            missing.append(pkg)
    if missing:
        ok = False
        print("\nKutubxonalar o‘rnatilmagan. Loyiha ildizida bajaring:")
        print("  pip install -r backend/requirements-dev.txt -r ai/requirements.txt "
              "--extra-index-url https://download.pytorch.org/whl/cpu")
    else:
        import torch

        print(f"\nPyTorch qurilmasi: {'GPU (CUDA) mavjud' if torch.cuda.is_available() else 'faqat CPU'}")

    model = ROOT / "artifacts" / "model.pt"
    manifest = ROOT / "data" / "raw" / "manifest.csv"
    print(f"\nO‘qitilgan model (artifacts/model.pt): {'bor' if model.is_file() else 'YO‘Q — tahlil cheklangan holatda ishlaydi'}")
    print(f"Dataset manifesti (data/raw/manifest.csv): {'bor' if manifest.is_file() else 'YO‘Q — avval OAI ma’lumotlarini tayyorlang (docs/MODEL_OQITISH.md)'}")
    print("\nNatija:", "muhit tayyor" if ok else "kamchiliklarni bartaraf eting")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
