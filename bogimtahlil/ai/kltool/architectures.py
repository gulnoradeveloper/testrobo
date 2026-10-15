"""Qo‘llab-quvvatlanadigan neyron tarmoq arxitekturalari."""
from __future__ import annotations

import torch.nn as nn
from torchvision import models

from . import NUM_CLASSES

SUPPORTED_ARCHITECTURES = ("resnet18", "efficientnet_b0")

DISPLAY_NAMES = {
    "resnet18": "ResNet-18",
    "efficientnet_b0": "EfficientNet-B0",
}


def build_model(arch: str, num_classes: int = NUM_CLASSES, pretrained: bool = False) -> nn.Module:
    """Arxitekturani yaratadi. pretrained=True — ImageNet vaznlari (internet talab qilinadi)."""
    if arch == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if arch == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Qo‘llab-quvvatlanmaydigan arxitektura: {arch}")


def gradcam_target_layer(model: nn.Module, arch: str) -> nn.Module:
    """Grad-CAM uchun oxirgi konvolyutsion blok."""
    if arch == "resnet18":
        return model.layer4[-1]
    if arch == "efficientnet_b0":
        return model.features[-1]
    raise ValueError(f"Qo‘llab-quvvatlanmaydigan arxitektura: {arch}")
