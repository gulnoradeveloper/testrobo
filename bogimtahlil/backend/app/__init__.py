"""Bo‘g‘imTahlil backend (FastAPI)."""
import sys
from pathlib import Path

# Umumiy AI moduli (kltool) loyiha ildizidagi ai/ katalogida joylashgan.
# Docker obrazida kltool to‘g‘ridan-to‘g‘ri /app ga nusxalanadi.
_AI_DIR = Path(__file__).resolve().parents[2] / "ai"
if _AI_DIR.is_dir() and str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

__version__ = "1.0.0"
