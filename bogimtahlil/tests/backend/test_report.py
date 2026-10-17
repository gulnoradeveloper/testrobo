import io
from datetime import datetime, timezone

from PIL import Image

from app.services.report import FOOTER_TEXT, build_report
from conftest import make_xray_like


def _analysis():
    probs = [0.1, 0.15, 0.5, 0.2, 0.05]
    return {
        "id": "11111111-2222-3333-4444-555555555555", "number": "BT-20261015-111111",
        "created_at": datetime(2026, 10, 15, 9, 30, tzinfo=timezone.utc).isoformat(),
        "image": {"image_id": "abcdef123456", "width": 480, "height": 400},
        "prediction": {"kl_grade": 2, "label": "KL2", "title": "Yengil o‘zgarishlar", "description": "Ta’rif"},
        "probabilities": [{"grade": i, "label": f"KL{i}", "title": f"Daraja {i}", "probability": p} for i, p in enumerate(probs)],
        "model": {"name": "Bo‘g‘imTahlil", "architecture": "ResNet-18", "version": "v1", "checkpoint_sha256": "0" * 64,
                  "training_status": "trained"},
    }


def _pdf_text(pdf: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)


def test_report_builds_a4_pdf(tmp_path):
    orig = tmp_path / "o.png"
    Image.fromarray(make_xray_like()).save(orig)
    pdf = build_report(_analysis(), orig, orig)
    assert pdf.startswith(b"%PDF") and b"/MediaBox [ 0 0 595.2756 841.8898 ]" in pdf
    assert b"OpenSans" in pdf  # o‘zbekcha harflar uchun TTF shrift joylashtirilgan
    text = _pdf_text(pdf)
    if text:
        for s in ("BO‘G‘IMTAHLIL", "KL2", "Yengil o‘zgarishlar", "BT-20261015-111111", FOOTER_TEXT[:40]):
            assert s in text.replace("\n", " "), s


def test_report_without_heatmap(tmp_path):
    orig = tmp_path / "o.png"
    Image.fromarray(make_xray_like()).save(orig)
    assert build_report(_analysis(), orig, None).startswith(b"%PDF")


def test_report_module_has_no_tz_database_dependency():
    # Windows’da tzdata bo‘lmaydi — modul ZoneInfo ishlatmasligi kerak
    import inspect

    import app.services.report as r

    src = inspect.getsource(r)
    assert "from zoneinfo" not in src and "import zoneinfo" not in src
    assert r.TZ.utcoffset(None).total_seconds() == 5 * 3600
