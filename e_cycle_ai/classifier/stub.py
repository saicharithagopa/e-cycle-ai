"""Deterministic stub classifier for the Milestone 2 vertical slice.

Returns a fixed, plausible ranking so the full pipeline
(upload -> classify -> confirm -> enrich -> score -> explain) can be
exercised end to end before the real model is trained in Milestone 3.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from .base import ClassificationResult, InvalidImageError


class StubClassifier:
    """Stub implementation of the DeviceClassifier protocol."""

    model_version = "stub-0.1.0"

    # Fixed ranking keeps integration tests deterministic.
    _RANKING = (("laptop", 0.92), ("tablet", 0.06), ("phone", 0.02))

    def analyze(self, image_bytes: bytes) -> list[ClassificationResult]:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError(
                "Upload a clear JPEG, PNG, or WebP photo of the device."
            ) from exc
        return [
            ClassificationResult(
                device_class=name, confidence=conf, model_version=self.model_version
            )
            for name, conf in self._RANKING
        ]


def get_classifier() -> StubClassifier:
    """Factory: swap in the trained model here in Milestone 3."""
    return StubClassifier()
