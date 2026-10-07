"""SQLAlchemy ORM models — Milestone 2 starter schema.

Mirrors the core data model from Milestone 1 (Product Vision & Requirements):
DeviceClass, DeviceProfile, MaterialProfile (embedded as JSON on the profile
for the starter slice), ScoringRule, Assessment, Prediction, Recommendation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class DeviceClass(Base):
    """A supported device category (e.g. laptop, phone, tablet)."""

    __tablename__ = "device_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128))
    supported: Mapped[bool] = mapped_column(default=True)

    profiles: Mapped[list["DeviceProfile"]] = relationship(back_populates="device_class")


class DeviceProfile(Base):
    """Versioned, curated knowledge for one device class.

    Components, materials and hazards are stored as JSON documents so the
    knowledge base can evolve without schema migrations; they are always
    labeled as category-level estimates, never measurements of a unit.
    """

    __tablename__ = "device_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_class_id: Mapped[int] = mapped_column(
        ForeignKey("device_classes.id"), index=True
    )
    version: Mapped[str] = mapped_column(String(32))
    components_json: Mapped[str] = mapped_column(Text)  # JSON list of {name, notes}
    materials_json: Mapped[str] = mapped_column(Text)  # JSON list of {material, category, recovery_relevance}
    hazards_json: Mapped[str] = mapped_column(Text)  # JSON list of strings
    caveats: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    device_class: Mapped[DeviceClass] = relationship(back_populates="profiles")


class ScoringRule(Base):
    """One versioned scoring factor and its weight in the Circularity Score."""

    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    factor: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    weight: Mapped[float] = mapped_column(Float)
    version: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text, default="")


class Assessment(Base):
    """One user assessment: image (never persisted) plus condition facts."""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_class: Mapped[str] = mapped_column(String(64), index=True)
    age_years: Mapped[int] = mapped_column(Integer)
    powers_on: Mapped[bool] = mapped_column()
    condition: Mapped[str] = mapped_column(String(64))
    image_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    prediction: Mapped["Prediction | None"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    recommendation: Mapped["Recommendation | None"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )


class Prediction(Base):
    """Classifier output for one assessment."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"), unique=True, index=True
    )
    device_class: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64))

    assessment: Mapped[Assessment] = relationship(back_populates="prediction")


class Recommendation(Base):
    """Decision-engine output for one assessment."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"), unique=True, index=True
    )
    pathway: Mapped[str] = mapped_column(String(32))  # repair | reuse | recycle
    score: Mapped[float] = mapped_column(Float)  # 0..100 Circularity Score
    factors_json: Mapped[str] = mapped_column(Text)  # JSON {factor: contribution}
    explanation_version: Mapped[str] = mapped_column(String(64))
    explanation: Mapped[str] = mapped_column(Text)

    assessment: Mapped[Assessment] = relationship(back_populates="recommendation")
