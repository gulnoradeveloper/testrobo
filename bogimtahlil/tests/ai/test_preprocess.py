import numpy as np
import pytest

from kltool.preprocess import (DEFAULT_CONFIG, PREPROCESS_VERSION, PreprocessConfig, decode_grayscale,
                               heatmap_to_original, letterbox, preprocess_array)
from conftest import encode, make_xray_like


def test_output_shape_and_dtype():
    x, meta = preprocess_array(make_xray_like(480, 300))
    assert x.shape == (3, 224, 224)
    assert x.dtype == np.float32
    assert (meta.orig_width, meta.orig_height) == (480, 300)


def test_letterbox_keeps_whole_image_no_crop():
    gray = np.zeros((100, 300), np.uint8)
    gray[:, 0] = 255  # chap chekka
    gray[:, -1] = 255  # o‘ng chekka
    boxed, meta = letterbox(gray, DEFAULT_CONFIG)
    assert boxed.shape == (224, 224)
    # Kesilmagan: ikkala chekka ham natijada saqlangan
    assert boxed[:, 0].max() > 100 and boxed[:, -1].max() > 100
    assert meta.pad_top == 100 and meta.pad_left == 0 and meta.side == 300


def test_normalization_uses_config():
    x, _ = preprocess_array(np.full((50, 50), 255, np.uint8))
    expected = (1.0 - np.array(DEFAULT_CONFIG.mean)) / np.array(DEFAULT_CONFIG.std)
    assert np.allclose(x[:, 112, 112], expected, atol=1e-5)


def test_rgb_and_gray_decode_identically():
    gray = make_xray_like(200, 200)
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    a = decode_grayscale(encode(gray))
    b = decode_grayscale(encode(rgb))
    assert a.shape == b.shape == (200, 200)
    assert np.abs(a.astype(int) - b.astype(int)).max() <= 1


def test_heatmap_maps_back_to_original_geometry():
    _, meta = letterbox(np.zeros((150, 400), np.uint8))
    cam = np.zeros((224, 224), np.float32)
    cam[112, :] = 1.0
    full = heatmap_to_original(cam, meta)
    assert full.shape == (150, 400)
    assert 0.0 <= full.min() and full.max() <= 1.0


def test_config_roundtrip():
    d = DEFAULT_CONFIG.to_dict()
    assert PreprocessConfig.from_dict(d) == DEFAULT_CONFIG
    assert d["version"] == PREPROCESS_VERSION


def test_letterbox_rejects_color_array():
    with pytest.raises(ValueError):
        letterbox(np.zeros((10, 10, 3), np.uint8))
