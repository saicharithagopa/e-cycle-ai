"""Application configuration loaded from the environment with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Override with environment variables in production."""

    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./e_cycle_ai.db")
    )
    upload_max_mb: int = field(
        default_factory=lambda: _env_int("UPLOAD_MAX_MB", 10)
    )
    image_retention_hours: int = field(
        default_factory=lambda: _env_int("IMAGE_RETENTION_HOURS", 24)
    )
    scoring_version: str = "0.2.0"
    knowledge_version: str = "0.2.0"
    classifier_version: str = "stub-0.1.0"
    allowed_image_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )


settings = Settings()
