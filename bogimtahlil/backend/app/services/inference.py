"""Model xizmati: server ishga tushganda modelni bir marta yuklaydi va so‘rovlarda qayta ishlatadi."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import numpy as np
import torch

from kltool.architectures import DISPLAY_NAMES, gradcam_target_layer
from kltool.checkpoint import TRAINED, CheckpointError, LoadedModel, load_checkpoint
from kltool.gradcam import GradCAM
from kltool.preprocess import heatmap_to_original, preprocess_array

from ..config import Settings
from ..errors import ApiError

log = logging.getLogger("bogimtahlil.model")


@dataclass
class Prediction:
    probabilities: list[float]
    predicted_class: int
    cam: np.ndarray | None  # asl tasvir o‘lchamidagi [0..1] xarita
    gradcam_error: str | None  # None | GRADCAM_FAILED | GRADCAM_EMPTY
    timing_ms: dict[str, float]


class ModelService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loaded: LoadedModel | None = None
        self.error_code: str | None = None
        self.error_message: str | None = None
        self.device = torch.device("cpu")
        self._lock = threading.Lock()  # Grad-CAM hooklari tufayli bir vaqtda bitta inference
        self._gradcam: GradCAM | None = None

    def load(self) -> None:
        s = self.settings
        if s.torch_threads > 0:
            torch.set_num_threads(s.torch_threads)
        if s.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(s.device)
        try:
            self.loaded = load_checkpoint(
                s.model_path, device=self.device, expected_sha256=s.model_sha256,
                allow_untrained=s.allow_untrained_model,
            )
        except CheckpointError as exc:
            self.loaded = None
            self.error_code, self.error_message = exc.code, exc.message
            log.warning("Model yuklanmadi: %s — %s", exc.code, exc.message)
            return
        for p in self.loaded.model.parameters():
            p.requires_grad_(True)  # Grad-CAM uchun gradient kerak
        self._gradcam = GradCAM(self.loaded.model, gradcam_target_layer(self.loaded.model, self.loaded.architecture))
        self.error_code = self.error_message = None
        log.info("Model yuklandi: %s (%s), sha256=%s, qurilma=%s", self.loaded.model_version,
                 self.loaded.architecture, self.loaded.sha256[:12], self.device)

    @property
    def ready(self) -> bool:
        return self.loaded is not None

    @property
    def is_trained(self) -> bool:
        return self.loaded is not None and self.loaded.training_status == TRAINED

    @property
    def display_architecture(self) -> str | None:
        return DISPLAY_NAMES.get(self.loaded.architecture) if self.loaded else None

    def require(self) -> LoadedModel:
        if self.loaded is None:
            raise ApiError("MODEL_NOT_READY", 503, details={"reason": self.error_code})
        return self.loaded

    def predict(self, gray: np.ndarray, with_gradcam: bool = True) -> Prediction:
        lm = self.require()
        timing: dict[str, float] = {}
        with self._lock:
            t0 = time.perf_counter()
            x, meta = preprocess_array(gray, lm.preprocess)
            xt = torch.from_numpy(x)[None].to(self.device)
            timing["preprocess_ms"] = (time.perf_counter() - t0) * 1000

            t1 = time.perf_counter()
            with torch.inference_mode():
                logits = lm.model(xt)
                probs = torch.softmax(logits.float(), dim=1)[0].cpu().numpy().astype(np.float64)
            timing["inference_ms"] = (time.perf_counter() - t1) * 1000
            if probs.shape != (len(lm.class_names),) or not np.all(np.isfinite(probs)):
                raise ApiError("ANALYSIS_FAILED", 500, details={"reason": "model chiqishi noto‘g‘ri shaklda"})
            pred = int(np.argmax(probs))

            cam_full, cam_error = None, None
            if with_gradcam and self._gradcam is not None:
                t2 = time.perf_counter()
                try:
                    cam, _ = self._gradcam(xt, pred)
                    if float(cam.max()) <= 0.0:
                        # Barcha gradient-vaznli aktivatsiyalar manfiy yoki nol — ko‘rsatadigan soha yo‘q
                        cam_error = "GRADCAM_EMPTY"
                    else:
                        cam_full = heatmap_to_original(cam, meta)
                except Exception:  # Grad-CAM xatosi bashoratni bekor qilmaydi, lekin ochiq bildiriladi
                    log.exception("Grad-CAM xatosi")
                    cam_error = "GRADCAM_FAILED"
                timing["gradcam_ms"] = (time.perf_counter() - t2) * 1000
        return Prediction(probs.tolist(), pred, cam_full, cam_error, timing)
