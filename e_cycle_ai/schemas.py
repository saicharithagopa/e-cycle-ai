"""Pydantic schemas for API input validation and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceClassOut(BaseModel):
    name: str
    label: str
    supported: bool

    model_config = {"from_attributes": True}


class FactorBreakdown(BaseModel):
    repairability: float = Field(ge=0, le=1)
    reuse: float = Field(ge=0, le=1)
    recyclability: float = Field(ge=0, le=1)
    recovery: float = Field(ge=0, le=1)


class AnalyzeResponse(BaseModel):
    assessment_id: int
    predicted_class: str
    confidence: float
    pathway: str
    circularity_score: float
    factors: FactorBreakdown
    explanation: str
    model_version: str
    knowledge_version: str
    scoring_version: str


class AssessmentDetail(BaseModel):
    assessment_id: int
    device_class: str
    age_years: int
    powers_on: bool
    condition: str
    predicted_class: str | None = None
    confidence: float | None = None
    pathway: str | None = None
    circularity_score: float | None = None
