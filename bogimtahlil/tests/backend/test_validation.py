import io

import numpy as np
import pytest
from PIL import Image

from app.errors import ApiError
from app.services.validation import validate_upload
from conftest import encode, make_xray_like

MB = 1024 * 1024


def v(data, name="a.png", mime="image/png", max_bytes=20 * MB, max_pixels=50_000_000, min_side=128):
    return validate_upload(data, name, mime, max_bytes, max_pixels, min_side)


def code(fn):
    with pytest.raises(ApiError) as e:
        fn()
    return e.value.code


def test_valid_png_and_jpeg(png_bytes, jpeg_bytes):
    r = v(png_bytes)
    assert (r.width, r.height, r.fmt) == (480, 400, "png") and r.gray.shape == (400, 480)
    assert v(jpeg_bytes, "a.JPG", "image/jpeg").fmt == "jpeg"


def test_empty_file():
    assert code(lambda: v(b"")) == "NO_FILE"


def test_too_large(png_bytes):
    assert code(lambda: v(png_bytes, max_bytes=100)) == "FILE_TOO_LARGE"


@pytest.mark.parametrize("data,name,mime", [
    (b"GIF89a" + b"\0" * 100, "a.gif", "image/gif"),
    (b"%PDF-1.4 ...", "a.pdf", "application/pdf"),
    (b"#!/bin/sh\nrm -rf /", "a.png", "image/png"),
    (b"MZ\x90\x00" + b"\0" * 100, "a.exe", "application/octet-stream"),
])
def test_unsupported_format(data, name, mime):
    assert code(lambda: v(data, name, mime)) == "UNSUPPORTED_FORMAT"


def test_extension_mime_mismatch(png_bytes):
    assert code(lambda: v(png_bytes, "a.jpg", "image/png")) == "UNSUPPORTED_FORMAT"
    assert code(lambda: v(png_bytes, "a.png", "image/jpeg")) == "UNSUPPORTED_FORMAT"
    assert code(lambda: v(png_bytes, "a.dcm", "image/png")) == "UNSUPPORTED_FORMAT"


def test_truncated_image(png_bytes, jpeg_bytes):
    assert code(lambda: v(png_bytes[: len(png_bytes) // 2])) == "IMAGE_UNREADABLE"
    assert code(lambda: v(jpeg_bytes[:400], "a.jpg", "image/jpeg")) == "IMAGE_UNREADABLE"


def test_blank_image_rejected():
    assert code(lambda: v(encode(np.full((300, 300), 128, np.uint8)))) == "IMAGE_UNREADABLE"


def test_too_small_and_too_many_pixels():
    assert code(lambda: v(encode(make_xray_like(100, 100)))) == "IMAGE_DIMENSIONS"
    assert code(lambda: v(encode(make_xray_like(600, 600)), max_pixels=100_000)) == "IMAGE_DIMENSIONS"


def test_rgba_png_accepted():
    rgba = np.dstack([np.repeat(make_xray_like()[:, :, None], 3, 2), np.full((400, 480), 255, np.uint8)])
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG")
    assert v(buf.getvalue()).gray.ndim == 2
