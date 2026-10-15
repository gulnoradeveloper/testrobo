"""Grad-CAM (Selvaraju va boshq., 2017) — tanlangan sinf uchun e’tibor xaritasi."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer

    def __call__(self, x: torch.Tensor, class_idx: int) -> tuple[np.ndarray, torch.Tensor]:
        """x: 1×3×H×W. Qaytaradi: (H×W [0..1] xarita, logits)."""
        activations: list[torch.Tensor] = []
        gradients: list[torch.Tensor] = []

        def fwd_hook(_m, _i, out):
            activations.append(out)
            out.register_hook(lambda g: gradients.append(g))

        handle = self.target_layer.register_forward_hook(fwd_hook)
        try:
            self.model.zero_grad(set_to_none=True)
            with torch.enable_grad():
                logits = self.model(x)
                logits[0, class_idx].backward()
        finally:
            handle.remove()

        if not activations or not gradients:
            raise RuntimeError("Grad-CAM uchun aktivatsiya yoki gradient olinmadi")
        act = activations[0].detach()[0]  # C×h×w
        grad = gradients[0].detach()[0]
        weights = grad.mean(dim=(1, 2))
        cam = F.relu((weights[:, None, None] * act).sum(dim=0))
        cam = F.interpolate(cam[None, None], size=x.shape[-2:], mode="bilinear", align_corners=False)[0, 0]
        cam = cam.cpu().numpy()
        cmax = float(cam.max())
        cam = cam / cmax if cmax > 1e-8 else np.zeros_like(cam)
        self.model.zero_grad(set_to_none=True)
        return cam.astype(np.float32), logits.detach()


def colorize(cam: np.ndarray) -> np.ndarray:
    """[0..1] xarita → RGB uint8 (JET palitrasi)."""
    import cv2

    heat = cv2.applyColorMap((np.clip(cam, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)


def overlay(gray: np.ndarray, cam: np.ndarray, alpha: float = 0.4) -> np.ndarray:
    """Grayscale asl tasvir ustiga rangli xaritani ustma-ust qo‘yish (RGB uint8)."""
    base = np.repeat(gray[:, :, None], 3, axis=2).astype(np.float32)
    heat = colorize(cam).astype(np.float32)
    out = (1 - alpha) * base + alpha * heat
    return np.clip(out, 0, 255).astype(np.uint8)
