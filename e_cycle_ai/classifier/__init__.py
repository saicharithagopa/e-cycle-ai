"""Image-classification module boundary."""

from .base import ClassificationResult, DeviceClassifier
from .stub import StubClassifier

__all__ = ["ClassificationResult", "DeviceClassifier", "StubClassifier"]
