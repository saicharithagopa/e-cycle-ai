"""Seed the database with supported device classes, a curated laptop profile,
and the versioned scoring rules. Idempotent: safe to run on every startup."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine
from .decision.engine import FACTOR_WEIGHTS, SCORING_VERSION
from .models import DeviceClass, DeviceProfile, ScoringRule

KNOWLEDGE_VERSION = "0.2.0"

_DEVICE_CLASSES = [
    ("laptop", "Laptop computer", True),
    ("phone", "Mobile phone", True),
    ("tablet", "Tablet", True),
    ("charger", "Charger / power adapter", True),
    ("battery", "Battery pack", True),
]

_LAPTOP_PROFILE = {
    "components": [
        {"name": "Display panel", "notes": "Often the most valuable reusable part."},
        {"name": "Lithium-ion battery", "notes": "Requires careful handling; do not puncture."},
        {"name": "Mainboard", "notes": "Contains recoverable copper and trace precious metals."},
        {"name": "Storage drive", "notes": "Sanitize or destroy before disposition."},
        {"name": "Chassis / enclosure", "notes": "Aluminum or plastic; recyclable where facilities exist."},
    ],
    "materials": [
        {"material": "Aluminum", "category": "structural metal", "recovery_relevance": "high"},
        {"material": "Copper", "category": "conductor", "recovery_relevance": "high"},
        {"material": "Lithium", "category": "battery chemistry", "recovery_relevance": "medium"},
        {"material": "Glass", "category": "display", "recovery_relevance": "low"},
        {"material": "Plastics (ABS/PC)", "category": "enclosure", "recovery_relevance": "low"},
    ],
    "hazards": [
        "Lithium-ion battery: do not puncture, crush, or incinerate.",
        "Wipe or destroy storage media before recycling or donation.",
    ],
    "caveats": (
        "Values are typical for the laptop category and are not measurements "
        "of the submitted unit. A photograph cannot determine exact material quantities."
    ),
}


def seed_db(db: Session) -> None:
    """Insert seed data only when the tables are empty."""
    if db.execute(select(DeviceClass)).first() is not None:
        return

    for name, label, supported in _DEVICE_CLASSES:
        db.add(DeviceClass(name=name, label=label, supported=supported))
    db.flush()

    laptop = db.execute(
        select(DeviceClass).where(DeviceClass.name == "laptop")
    ).scalar_one()
    db.add(
        DeviceProfile(
            device_class_id=laptop.id,
            version=KNOWLEDGE_VERSION,
            components_json=json.dumps(_LAPTOP_PROFILE["components"]),
            materials_json=json.dumps(_LAPTOP_PROFILE["materials"]),
            hazards_json=json.dumps(_LAPTOP_PROFILE["hazards"]),
            caveats=_LAPTOP_PROFILE["caveats"],
        )
    )

    descriptions = {
        "repairability": "Likelihood the device can be returned to service economically.",
        "reuse": "Potential for continued or second-life use.",
        "recyclability": "Ease of responsible material recovery at end of life.",
        "recovery": "Typical material value recoverable from the category.",
    }
    for factor, weight in FACTOR_WEIGHTS.items():
        db.add(
            ScoringRule(
                factor=factor,
                weight=weight,
                version=SCORING_VERSION,
                description=descriptions[factor],
            )
        )
    db.commit()


def init_db() -> None:
    """Create tables and seed. Called on application startup."""
    Base.metadata.create_all(bind=engine)
    from .db import SessionLocal

    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")
