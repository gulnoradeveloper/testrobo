"""Integration testlari: Backend → AI → Natijalar → PDF → Sessiya tarixi."""
import json
import re
from datetime import datetime, timedelta, timezone

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image
import io

from conftest import encode, make_settings, make_xray_like, upload


def test_health_and_model_info(client):
    h = client.get("/api/v1/health").json()
    assert h["status"] == "ok" and h["model_loaded"] is True
    assert h["model_trained"] is False  # test fixture o‘qitilmagan deb ochiq ko‘rsatiladi
    info = client.get("/api/v1/model/info").json()
    assert info["class_names"] == ["KL0", "KL1", "KL2", "KL3", "KL4"]
    assert info["architecture"] == "ResNet-18" and len(info["checkpoint_sha256"]) == 64
    assert info["metrics"] == {} and info["calibration_evaluated"] is False
    assert "test" in info["status_message"] or "o‘qitilgan model emas" in info["status_message"]


def test_full_analysis_flow(client, png_bytes):
    r = upload(client, png_bytes)
    assert r.status_code == 201, r.text
    a = r.json()
    assert re.fullmatch(r"[0-9a-f-]{36}", a["id"]) and a["status"] == "completed"
    probs = [p["probability"] for p in a["probabilities"]]
    assert len(probs) == 5 and abs(sum(probs) - 1) < 1e-6
    assert a["prediction"]["kl_grade"] == int(np.argmax(probs))
    assert a["prediction"]["label"] == f"KL{a['prediction']['kl_grade']}"
    assert a["model"]["training_status"] == "untrained-test-fixture"
    assert a["image"]["width"] == 480 and a["image"]["height"] == 400
    assert a["heatmap"]["available"] is True
    assert {"preprocess_ms", "inference_ms", "gradcam_ms", "total_ms"} <= set(a["timing"])
    assert "shifokor tashxisi o‘rnini bosmaydi" in a["disclaimer"]

    assert client.get(f"/api/v1/analyses/{a['id']}").json()["probabilities"] == a["probabilities"]

    img = client.get(a["image"]["url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(img.content)).size == (480, 400)

    heat = client.get(a["heatmap"]["heatmap_url"])
    hm = Image.open(io.BytesIO(heat.content))
    assert hm.mode == "RGBA" and hm.size == (480, 400)  # asl tasvir koordinatalarida
    ov = Image.open(io.BytesIO(client.get(a["heatmap"]["overlay_url"]).content))
    assert ov.mode == "RGB" and ov.size == (480, 400)

    rep = client.get(a["report_url"])
    assert rep.status_code == 200 and rep.headers["content-type"] == "application/pdf"
    assert rep.content.startswith(b"%PDF") and len(rep.content) > 10_000
    assert "attachment" in rep.headers["content-disposition"]
    assert client.get(a["report_url"]).content == rep.content  # keshlangan hisobot


def test_prediction_matches_direct_model(client, png_bytes, fixture_checkpoint):
    """API qaytargan ehtimolliklar aynan modeldan olingan bo‘lishi kerak (soxta qiymat emas)."""
    import torch

    from kltool.checkpoint import load_checkpoint
    from kltool.preprocess import decode_grayscale, preprocess_array

    lm = load_checkpoint(fixture_checkpoint, allow_untrained=True)
    x, _ = preprocess_array(decode_grayscale(png_bytes))
    with torch.inference_mode():
        expected = torch.softmax(lm.model(torch.from_numpy(x)[None]), 1)[0].numpy()
    got = [p["probability"] for p in upload(client, png_bytes).json()["probabilities"]]
    assert np.allclose(got, expected, atol=1e-5)


def test_different_images_give_different_outputs(client):
    a = upload(client, encode(make_xray_like(seed=3))).json()
    b = upload(client, encode(255 - make_xray_like(seed=4))).json()
    assert a["probabilities"] != b["probabilities"]


def test_jpeg_upload(client, jpeg_bytes):
    assert upload(client, jpeg_bytes, "knee.jpeg", "image/jpeg").status_code == 201


def test_error_format_and_messages(client, png_bytes):
    r = client.post("/api/v1/analyses", data={"projection_confirmed": "true"})
    assert r.status_code == 400 and r.json() == {"error": {"code": "NO_FILE", "message": "Fayl tanlanmagan."}}
    r = upload(client, b"%PDF-1.4", "a.pdf", "application/pdf")
    assert r.status_code == 415 and r.json()["error"]["message"] == "Fayl formati qo‘llab-quvvatlanmaydi."
    r = upload(client, png_bytes[:300])
    assert r.status_code == 422 and r.json()["error"]["message"] == "Tasvirni o‘qib bo‘lmadi."
    r = upload(client, png_bytes, confirmed=False)
    assert r.status_code == 422 and r.json()["error"]["code"] == "PROJECTION_NOT_CONFIRMED"
    r = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404 and r.json()["error"]["message"] == "Tahlil natijasi topilmadi."
    assert client.get("/api/v1/analyses/../../etc/passwd").status_code == 404
    assert client.get("/api/v1/analyses/not-a-uuid").json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/v1/yoq").json()["error"]["code"] == "ROUTE_NOT_FOUND"


def test_file_too_large(tmp_path, fixture_checkpoint):
    from app.main import create_app

    with TestClient(create_app(make_settings(tmp_path, fixture_checkpoint, max_upload_mb=1))) as c:
        big = encode(np.random.default_rng(0).integers(0, 255, (1200, 1200), dtype=np.uint8))
        assert len(big) > 1024 * 1024
        r = upload(c, big)
        assert r.status_code == 413 and r.json()["error"]["message"] == "Fayl hajmi belgilangan chegaradan oshgan."


def test_no_model_no_fake_result(client_no_model, png_bytes):
    h = client_no_model.get("/api/v1/health").json()
    assert h["model_loaded"] is False
    assert h["model_status_message"] == "Model hali o‘qitilmagan: artifacts/model.pt mavjud emas."
    info = client_no_model.get("/api/v1/model/info").json()
    assert info["loaded"] is False and info["status_code"] == "MODEL_NOT_FOUND" and info["version"] is None
    r = upload(client_no_model, png_bytes)
    assert r.status_code == 503
    assert r.json()["error"]["message"] == "Sun’iy intellekt modeli hali tayyor emas."
    assert client_no_model.get("/api/v1/analyses").json() == {"items": [], "total": 0}


def test_untrained_checkpoint_refused_by_default(tmp_path, fixture_checkpoint, png_bytes):
    from app.main import create_app

    with TestClient(create_app(make_settings(tmp_path, fixture_checkpoint, allow_untrained_model=False))) as c:
        assert c.get("/api/v1/model/info").json()["status_code"] == "MODEL_NOT_TRAINED"
        assert upload(c, png_bytes).status_code == 503


def test_incompatible_checkpoint_refused(tmp_path, fixture_checkpoint, png_bytes):
    import torch

    from app.main import create_app

    bad = tmp_path / "bad.pt"
    payload = torch.load(fixture_checkpoint, weights_only=True)
    payload["class_names"] = ["A", "B", "C", "D", "E"]
    torch.save(payload, bad)
    with TestClient(create_app(make_settings(tmp_path, bad))) as c:
        assert c.get("/api/v1/model/info").json()["status_code"] == "MODEL_INCOMPATIBLE"
        assert upload(c, png_bytes).status_code == 503


def test_session_isolation_and_history(client, png_bytes, tmp_path):
    a1 = upload(client, png_bytes).json()
    a2 = upload(client, encode(make_xray_like(seed=9))).json()
    hist = client.get("/api/v1/analyses").json()
    assert hist["total"] == 2 and {i["id"] for i in hist["items"]} == {a1["id"], a2["id"]}
    assert hist["items"][0]["id"] == a2["id"]  # eng yangisi birinchi
    g = a1["prediction"]["kl_grade"]
    assert all(i["kl_grade"] == g for i in client.get(f"/api/v1/analyses?grade={g}").json()["items"])
    assert client.get("/api/v1/analyses?sort=oldest").json()["items"][0]["id"] == a1["id"]

    # Boshqa sessiya (yangi cookie)
    other = TestClient(client.app)
    assert other.get("/api/v1/analyses").json()["total"] == 0
    for path in ("", "/image", "/heatmap", "/report"):
        r = other.get(f"/api/v1/analyses/{a1['id']}{path}")
        assert r.status_code == 403
        assert r.json()["error"]["message"] == "Ushbu ma’lumotni ko‘rishga ruxsat yo‘q."
    assert other.delete(f"/api/v1/analyses/{a1['id']}").status_code == 403
    # Soxta cookie ham kirish bermaydi
    other.cookies.set("bt_session", "x" * 43)
    assert other.get(f"/api/v1/analyses/{a1['id']}").status_code == 403


def test_session_cookie_flags(client, png_bytes):
    fresh = TestClient(client.app)
    r = fresh.get("/api/v1/analyses")
    sc = r.headers["set-cookie"].lower()
    assert "httponly" in sc and "samesite=lax" in sc


def test_delete_removes_files_and_records(client, png_bytes):
    a = upload(client, png_bytes).json()
    client.get(a["report_url"])
    storage = client.app.state.storage
    d = storage.root / a["id"]
    assert {p.name for p in d.iterdir()} == {"original.png", "heatmap.png", "overlay.png", "report.pdf"}
    assert client.delete(f"/api/v1/analyses/{a['id']}").status_code == 204
    assert not d.exists()
    assert client.get(f"/api/v1/analyses/{a['id']}").status_code == 404
    from app.models import Artifact

    with client.app.state.session_factory() as db:
        assert db.query(Artifact).filter_by(analysis_id=a["id"]).count() == 0


def test_expired_data_is_purged(client, png_bytes):
    from app.models import Analysis
    from app.services.analysis import purge_expired

    a = upload(client, png_bytes).json()
    sf, storage = client.app.state.session_factory, client.app.state.storage
    with sf() as db:
        row = db.get(Analysis, a["id"])
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert client.get(f"/api/v1/analyses/{a['id']}").status_code == 404
    with sf() as db:
        assert purge_expired(db, storage) == 1
    assert not (storage.root / a["id"]).exists()


def test_db_stores_no_personal_data(client, png_bytes):
    from app.models import Analysis

    a = upload(client, png_bytes, name="Aliyev_Vali_AB1234567.png").json()
    with client.app.state.session_factory() as db:
        row = db.get(Analysis, a["id"])
        dumped = json.dumps({c.name: str(getattr(row, c.name)) for c in row.__table__.columns}, ensure_ascii=False)
    assert "Aliyev" not in dumped and "AB1234567" not in dumped
    assert len(row.session_id) == 64  # cookie tokeni emas, uning hashi
    assert client.cookies.get("bt_session") not in dumped
    # Saqlangan fayl nomi server tomonidan yaratiladi
    assert not any("Aliyev" in p.name for p in client.app.state.storage.root.rglob("*"))


def test_gradcam_failure_is_reported_not_hidden(client, png_bytes, monkeypatch):
    svc = client.app.state.model_service

    def boom(*a, **k):
        raise RuntimeError("test")

    monkeypatch.setattr(svc._gradcam, "__call__", boom, raising=False)
    monkeypatch.setattr(type(svc._gradcam), "__call__", lambda self, *a, **k: boom())
    a = upload(client, png_bytes).json()
    assert a["heatmap"]["available"] is False
    assert a["heatmap"]["error"] == "Faollik xaritasini yaratishda xatolik yuz berdi."
    r = client.get(f"/api/v1/analyses/{a['id']}/heatmap")
    assert r.status_code == 404 and r.json()["error"]["code"] == "GRADCAM_FAILED"
    assert client.get(a["report_url"]).status_code == 200  # hisobot xaritasiz yaratiladi


def test_rate_limit(tmp_path, fixture_checkpoint, png_bytes):
    from app.main import create_app

    with TestClient(create_app(make_settings(tmp_path, fixture_checkpoint, rate_limit_analyses_per_minute=2))) as c:
        assert upload(c, png_bytes).status_code == 201
        assert upload(c, png_bytes).status_code == 201
        r = upload(c, png_bytes)
        assert r.status_code == 429 and r.json()["error"]["code"] == "RATE_LIMITED" and "retry-after" in r.headers


def test_security_headers(client):
    r = client.get("/api/v1/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"


def test_model_loaded_once(client, png_bytes, monkeypatch):
    import kltool.checkpoint as ck

    calls = []
    monkeypatch.setattr(ck, "load_checkpoint", lambda *a, **k: calls.append(1))
    for _ in range(2):
        assert upload(client, png_bytes).status_code == 201
    assert calls == []


def test_empty_gradcam_is_reported(client, png_bytes, monkeypatch):
    import numpy as np

    svc = client.app.state.model_service
    monkeypatch.setattr(type(svc._gradcam), "__call__", lambda self, x, c: (np.zeros((224, 224), np.float32), None))
    a = upload(client, png_bytes).json()
    assert a["heatmap"]["available"] is False and "bo‘sh" in a["heatmap"]["error"]
    r = client.get(f"/api/v1/analyses/{a['id']}/heatmap")
    assert r.status_code == 404 and r.json()["error"]["code"] == "GRADCAM_EMPTY"


def test_backend_serves_built_frontend(tmp_path, fixture_checkpoint):
    from app.main import create_app

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>Bo‘g‘imTahlil</html>", encoding="utf-8")
    (dist / "assets" / "a.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("x")
    with TestClient(create_app(make_settings(tmp_path, fixture_checkpoint, frontend_dist=dist))) as c:
        assert "Bo‘g‘imTahlil" in c.get("/").text
        assert "Bo‘g‘imTahlil" in c.get("/natija/abc").text  # SPA marshruti
        assert c.get("/assets/a.js").text == "console.log(1)"
        assert "x" != c.get("/../secret.txt").text and "Bo‘g‘imTahlil" in c.get("/..%2Fsecret.txt").text
        assert c.get("/api/v1/yoq").json()["error"]["code"] == "ROUTE_NOT_FOUND"
        assert c.get("/api/v1/health").json()["status"] == "ok"


def test_service_worker_killswitch(client):
    r = client.get("/sw.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    assert "unregister()" in r.text and r.headers["cache-control"] == "no-store"


def test_static_mime_types_do_not_depend_on_os_registry(tmp_path, fixture_checkpoint, monkeypatch):
    import mimetypes

    from app.main import create_app

    # Windows reestrini taqlid qilish: .js → text/plain
    monkeypatch.setitem(mimetypes.types_map, ".js", "text/plain")
    import importlib

    import app.main as m

    importlib.reload(m)
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>")
    (dist / "assets" / "a.js").write_text("1")
    (dist / "logo.webp").write_bytes(b"RIFF0000WEBP")
    with TestClient(m.create_app(make_settings(tmp_path, fixture_checkpoint, frontend_dist=dist))) as c:
        assert "javascript" in c.get("/assets/a.js").headers["content-type"]
        assert c.get("/logo.webp").headers["content-type"] == "image/webp"


def test_default_sqlite_url_is_posix():
    from app.config import Settings

    assert "\\" not in Settings().database_url and Settings().database_url.startswith("sqlite:///")


def test_server_starts_when_torch_dll_fails(tmp_path, fixture_checkpoint, monkeypatch):
    """Windows: PyTorch o‘rnatilgan, lekin DLL yuklanmaydi (OSError) — server baribir ishlashi shart."""
    import builtins
    import sys

    from app.main import create_app

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "torch" or name.startswith("torch."):
            raise OSError('[WinError 126] Error loading "c10.dll"')
        return real_import(name, *a, **k)

    for mod in [m for m in sys.modules if m == "torch" or m.startswith("torch.")]:
        monkeypatch.delitem(sys.modules, mod)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with TestClient(create_app(make_settings(tmp_path, fixture_checkpoint))) as c:
        h = c.get("/api/v1/health").json()
        assert h["status"] == "ok" and h["model_loaded"] is False
        assert "Visual C++" in h["model_status_message"]
        assert c.get("/api/v1/model/info").json()["status_code"] == "AI_LIBRARIES_BROKEN"
