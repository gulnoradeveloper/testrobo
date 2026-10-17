"""/api/v1/model/experiments — ma’lumotlar faqat tajriba fayllaridan olinadi, yo‘q bo‘lsa uydirilmaydi."""
import json

from fastapi.testclient import TestClient

from conftest import make_settings


def _client(tmp_path, model_path, **kw):
    from app.main import create_app

    return TestClient(create_app(make_settings(tmp_path, model_path, allow_untrained_model=False, **kw)))


def test_no_experiments_no_fake_numbers(tmp_path):
    with _client(tmp_path, tmp_path / "yoq.pt", experiments_dir=tmp_path / "exp", splits_dir=tmp_path / "spl") as c:
        e = c.get("/api/v1/model/experiments").json()
        info = c.get("/api/v1/model/info").json()
    assert e["dataset"]["available"] is False and e["comparison"]["available"] is False
    assert e["test"] == {"available": False}
    for arch in ("resnet18", "efficientnet_b0"):
        assert e["training"][arch]["available"] is False and e["training"][arch]["history"] == []
        assert e["training"][arch]["validation"] is None
    assert info["loaded"] is False and info["status_code"] == "MODEL_NOT_FOUND"
    assert info["status_message"] == "Model hali o‘qitilmagan: artifacts/model.pt mavjud emas."


def _metrics(acc):
    cm = [[5, 1, 0, 0, 0], [1, 3, 1, 0, 0], [0, 1, 4, 0, 0], [0, 0, 0, 5, 0], [0, 0, 0, 1, 3]]
    return {"n_samples": 26, "n_patients": 7, "accuracy": acc, "balanced_accuracy": 0.7, "macro_precision": 0.71,
            "macro_recall": 0.7, "macro_f1": 0.69, "quadratic_weighted_kappa": 0.8,
            "per_class": {f"KL{i}": {"precision": 0.7, "recall": 0.1 * (i + 5), "f1": 0.7, "support": 5} for i in range(5)},
            "confusion_matrix": cm, "early_grade_confusion": {"error_rate_within_kl0_kl2": 0.25}}


def test_values_come_from_files(tmp_path):
    exp, spl = tmp_path / "exp", tmp_path / "spl"
    for arch, acc in (("resnet18", 0.61), ("efficientnet_b0", 0.64)):
        d = exp / arch
        d.mkdir(parents=True)
        (d / "history.csv").write_text("epoch,train_loss,val_loss,train_accuracy,val_accuracy,val_macro_f1,val_qwk\n"
                                       "1,1.5,1.4,0.3,0.35,0.3,0.4\n2,1.2,1.25,0.45,0.42,0.38,0.55\n")
        (d / "train_summary.json").write_text(json.dumps({"best_epoch": 2, "epochs_run": 2, "training_seconds": 120,
                                                          "pretrained": True}))
        (d / "eval_val.json").write_text(json.dumps(_metrics(acc)))
    (exp / "efficientnet_b0" / "eval_test.json").write_text(json.dumps(_metrics(0.66)))
    (exp / "model_comparison.json").write_text(json.dumps({"selected": "experiments/efficientnet_b0",
                                                           "selection_rule": "validation macro_f1",
                                                           "selected_reason": "EfficientNet-B0: eng yuqori"}))
    spl.mkdir()
    (spl / "dataset_report.json").write_text(json.dumps({
        "totals": {"images": 100, "patients": 40, "sources": {"OAI": 100}}, "split_source": "bemorlar bo‘yicha",
        "patient_leakage": {"n_patients_in_multiple_splits": 0},
        "splits": {"train": {"images": 70, "patients": 28, "classes": {"KL0": 30, "KL1": 15, "KL2": 12, "KL3": 8, "KL4": 5}}}}))
    with _client(tmp_path, tmp_path / "yoq.pt", experiments_dir=exp, splits_dir=spl) as c:
        e = c.get("/api/v1/model/experiments").json()
    assert e["dataset"]["images"] == 100 and e["dataset"]["splits"]["train"]["classes"]["KL4"] == 5
    r = e["training"]["resnet18"]
    assert r["available"] and len(r["history"]) == 2 and r["history"][1]["val_loss"] == 1.25
    assert r["validation"]["accuracy"] == 0.61 and r["training_minutes"] == 2.0
    assert e["training"]["efficientnet_b0"]["validation"]["accuracy"] == 0.64
    assert e["comparison"]["selected"] == "efficientnet_b0" and e["comparison"]["selected_title"] == "EfficientNet-B0"
    assert e["test"]["available"] and e["test"]["accuracy"] == 0.66 and e["test"]["confusion_matrix"][0] == [5, 1, 0, 0, 0]
    assert e["test"]["recall"]["KL0"] == 0.5


def test_test_metrics_prefer_loaded_model(tmp_path, fixture_checkpoint):
    import torch

    p = tmp_path / "m.pt"
    payload = torch.load(fixture_checkpoint, weights_only=True)
    payload.update(training_status="trained", metrics={"test": _metrics(0.77)}, dataset={"name": "OAI"})
    torch.save(payload, p)
    with _client(tmp_path, p, experiments_dir=tmp_path / "exp", splits_dir=tmp_path / "spl") as c:
        e = c.get("/api/v1/model/experiments").json()
    assert e["test"]["accuracy"] == 0.77 and e["dataset"]["name"] == "OAI"
