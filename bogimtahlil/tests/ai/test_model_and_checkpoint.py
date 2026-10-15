import numpy as np
import pytest
import torch

from kltool import KL_CLASSES
from kltool.architectures import build_model, gradcam_target_layer
from kltool.checkpoint import TRAINED, UNTRAINED_FIXTURE, CheckpointError, load_checkpoint, save_checkpoint, sha256_file
from kltool.gradcam import GradCAM, overlay
from kltool.preprocess import DEFAULT_CONFIG, preprocess_array
from conftest import make_xray_like


@pytest.mark.parametrize("arch", ["resnet18", "efficientnet_b0"])
def test_model_io_shapes(arch):
    m = build_model(arch).eval()
    with torch.no_grad():
        out = m(torch.zeros(2, 3, 224, 224))
    assert out.shape == (2, len(KL_CLASSES)) == (2, 5)


def test_probabilities_sum_to_one(fixture_checkpoint):
    lm = load_checkpoint(fixture_checkpoint, allow_untrained=True)
    x, _ = preprocess_array(make_xray_like())
    with torch.inference_mode():
        p = torch.softmax(lm.model(torch.from_numpy(x)[None]), 1)[0].numpy()
    assert p.shape == (5,)
    assert abs(p.sum() - 1.0) < 1e-5
    assert int(p.argmax()) in range(5)


def test_untrained_checkpoint_rejected_by_default(fixture_checkpoint):
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(fixture_checkpoint)
    assert e.value.code == "MODEL_NOT_TRAINED"


def test_missing_checkpoint(tmp_path):
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(tmp_path / "yoq.pt")
    assert e.value.code == "MODEL_NOT_FOUND"


def test_corrupted_checkpoint(tmp_path):
    p = tmp_path / "bad.pt"
    p.write_bytes(b"bu checkpoint emas")
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(p)
    assert e.value.code == "MODEL_CORRUPTED"


def test_hash_mismatch(fixture_checkpoint):
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(fixture_checkpoint, expected_sha256="0" * 64, allow_untrained=True)
    assert e.value.code == "MODEL_HASH_MISMATCH"
    lm = load_checkpoint(fixture_checkpoint, expected_sha256=sha256_file(fixture_checkpoint), allow_untrained=True)
    assert lm.sha256 == sha256_file(fixture_checkpoint)


def _tamper(src, dst, **changes):
    payload = torch.load(src, weights_only=True)
    payload.update(changes)
    torch.save(payload, dst)


@pytest.mark.parametrize("change", [
    {"class_names": ["KL4", "KL3", "KL2", "KL1", "KL0"]},
    {"architecture": "vgg16"},
    {"preprocess": {**DEFAULT_CONFIG.to_dict(), "version": "pp-v0"}},
    {"format_version": 99},
])
def test_incompatible_checkpoint(fixture_checkpoint, tmp_path, change):
    p = tmp_path / "x.pt"
    _tamper(fixture_checkpoint, p, **change)
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(p, allow_untrained=True)
    assert e.value.code == "MODEL_INCOMPATIBLE"


def test_architecture_weights_mismatch(fixture_checkpoint, tmp_path):
    p = tmp_path / "x.pt"
    _tamper(fixture_checkpoint, p, architecture="efficientnet_b0")
    with pytest.raises(CheckpointError) as e:
        load_checkpoint(p, allow_untrained=True)
    assert e.value.code == "MODEL_INCOMPATIBLE"


def test_trained_flag_roundtrip(tmp_path):
    p = tmp_path / "t.pt"
    save_checkpoint(p, build_model("efficientnet_b0"), "efficientnet_b0", "v-test", DEFAULT_CONFIG, training_status=TRAINED)
    lm = load_checkpoint(p)
    assert lm.training_status == TRAINED and lm.architecture == "efficientnet_b0"
    assert (tmp_path / "t.pt.sha256").read_text().startswith(lm.sha256)


@pytest.mark.parametrize("arch", ["resnet18", "efficientnet_b0"])
def test_gradcam(arch):
    torch.manual_seed(0)
    m = build_model(arch).eval()
    x, _ = preprocess_array(make_xray_like())
    cam, logits = GradCAM(m, gradcam_target_layer(m, arch))(torch.from_numpy(x)[None], 2)
    assert cam.shape == (224, 224)
    assert cam.min() >= 0 and cam.max() <= 1.0
    assert logits.shape == (1, 5)
    ov = overlay(make_xray_like(224, 224), cam)
    assert ov.shape == (224, 224, 3) and ov.dtype == np.uint8


def test_untrained_fixture_marker(fixture_checkpoint):
    assert load_checkpoint(fixture_checkpoint, allow_untrained=True).training_status == UNTRAINED_FIXTURE
