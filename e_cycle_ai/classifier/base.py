"""Classifier interface contract.

Interface: analyze(image_bytes) -> list of ranked ClassificationResult.
Any implementation (stub today, fine-tuned torchvision model in Milestone 3)
must honor this contract so the API layer never changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ClassificationResult:
    device_class: str
    confidence: float  # 0.0 .. 1.0
    model_version: str


class DeviceClassifier(Protocol):
    """Contract every classifier implementation must satisfy."""

    def analyze(self, image_bytes: bytes) -> list[ClassificationResult]:
        """Return ranked class predictions for the image bytes.

        Raises:
            InvalidImageError: the bytes are not a decodable image.
        """
        ...


class InvalidImageError(ValueError):
    """Raised when uploaded bytes cannot be decoded as an image."""
