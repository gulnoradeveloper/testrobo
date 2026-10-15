"""O‘qitilgan haqiqiy model bilan integratsiya testi (artifacts/model.pt mavjud bo‘lganda ishlaydi).

Bu test o‘qitilmagan fixture emas, aynan dasturga eksport qilingan modelni standart sozlamada
(allow_untrained_model=False) yuklaydi.
"""
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from conftest import make_settings, upload

MODEL = Path(__file__).resolve().parents[2] / "artifacts" / "model.pt"
pytestmark = pytest.mark.skipif(not MODEL.is_file(), reason="artifacts/model.pt mavjud emas — model hali o‘qitilmagan")


def test_real_model_end_to_end(tmp_path, png_bytes):
    import torch

    from app.main import create_app
    from kltool.checkpoint import load_checkpoint
    from kltool.preprocess import decode_grayscale, preprocess_array

    lm = load_checkpoint(MODEL)  # o‘qitilgan bo‘lishi shart
    assert lm.training_status == "trained" and lm.class_names == ["KL0", "KL1", "KL2", "KL3", "KL4"]
    assert "test" in lm.metrics, "eksport qilingan modelda yakuniy test metrikalari bo‘lishi shart"

    with TestClient(create_app(make_settings(tmp_path, MODEL, allow_untrained_model=False))) as c:
        info = c.get("/api/v1/model/info").json()
        assert info["loaded"] and info["trained"] and info["metrics"]["test"]["n_samples"] > 0
        a = upload(c, png_bytes).json()
        probs = np.array([p["probability"] for p in a["probabilities"]])
        x, _ = preprocess_array(decode_grayscale(png_bytes), lm.preprocess)
        with torch.inference_mode():
            expected = torch.softmax(lm.model(torch.from_numpy(x)[None]), 1)[0].numpy()
        assert np.allclose(probs, expected, atol=1e-5) and abs(probs.sum() - 1) < 1e-6
        assert a["prediction"]["kl_grade"] == int(expected.argmax())
        assert a["model"]["training_status"] == "trained"
        assert c.get(a["report_url"]).content.startswith(b"%PDF")
