"""Umumiy test fixturelari.

DIQQAT: testlarda ishlatiladigan checkpoint tasodifiy vaznli ResNet-18 bo‘lib,
"untrained-test-fixture" deb belgilanadi. U faqat dastur zanjirini (yuklash → inference →
Grad-CAM → PDF) tekshirish uchun; uning bashoratlari tibbiy ma’noga ega emas va
backend uni standart sozlamada (BT_ALLOW_UNTRAINED_MODEL=false) rad etadi.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "backend", ROOT / "ai"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def make_xray_like(width: int = 480, height: int = 400, seed: int = 0) -> np.ndarray:
    """Sintetik grayscale test tasviri (rentgen emas — faqat dastur zanjirini tekshirish uchun)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:height, 0:width]
    img = 60 + 120 * np.exp(-(((xx - width / 2) / (width / 5)) ** 2)) * (np.abs(yy - height / 2) > height / 20)
    img = img + rng.normal(0, 8, size=img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def encode(arr: np.ndarray, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture(scope="session")
def png_bytes() -> bytes:
    return encode(make_xray_like())


@pytest.fixture(scope="session")
def jpeg_bytes() -> bytes:
    return encode(make_xray_like(seed=1), "JPEG")


@pytest.fixture(scope="session")
def fixture_checkpoint(tmp_path_factory) -> Path:
    import torch

    from kltool.architectures import build_model
    from kltool.checkpoint import UNTRAINED_FIXTURE, save_checkpoint
    from kltool.preprocess import DEFAULT_CONFIG

    torch.manual_seed(0)
    path = tmp_path_factory.mktemp("ckpt") / "fixture.pt"
    model = build_model("resnet18", pretrained=False)
    save_checkpoint(path, model, "resnet18", "test-fixture-0.0.0", DEFAULT_CONFIG, training_status=UNTRAINED_FIXTURE,
                    dataset={"name": "yo‘q (test fixture)"}, metrics={})
    return path


def make_settings(tmp_path: Path, model_path: Path, **kw):
    from app.config import Settings

    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}", storage_dir=tmp_path / "storage", model_path=model_path,
        allow_untrained_model=kw.pop("allow_untrained_model", True), device="cpu",
        rate_limit_analyses_per_minute=kw.pop("rate_limit_analyses_per_minute", 1000),
        rate_limit_requests_per_minute=kw.pop("rate_limit_requests_per_minute", 10000), **kw,
    )


@pytest.fixture
def client(tmp_path, fixture_checkpoint):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(make_settings(tmp_path, fixture_checkpoint))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_no_model(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(make_settings(tmp_path, tmp_path / "missing.pt", allow_untrained_model=False))
    with TestClient(app) as c:
        yield c


def upload(c, data: bytes, name: str = "tizza.png", mime: str = "image/png", confirmed: bool = True):
    return c.post("/api/v1/analyses", files={"file": (name, data, mime)},
                  data={"projection_confirmed": "true" if confirmed else "false"})
