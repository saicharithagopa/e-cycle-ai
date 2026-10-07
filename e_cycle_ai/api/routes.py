"""REST API routes.

Routes:
    GET  /health
    GET  /api/v1/device-classes
    POST /api/v1/assessments/analyze   (multipart: image + condition fields)
    GET  /api/v1/assessments/{assessment_id}

The full pipeline per request:
    validate -> classify -> confirm class -> enrich (knowledge) ->
    score (decision engine) -> explain -> persist -> respond.
The uploaded image is never persisted (privacy by design).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..classifier.base import InvalidImageError
from ..classifier.stub import get_classifier
from ..config import settings
from ..db import get_db
from ..decision.engine import recommend
from ..knowledge.service import ProfileNotFoundError, get_profile
from ..models import Assessment, DeviceClass, Prediction, Recommendation
from ..schemas import AnalyzeResponse, AssessmentDetail, DeviceClassOut

router = APIRouter(prefix="/api/v1")


@router.get("/device-classes", response_model=list[DeviceClassOut])
def list_device_classes(db: Session = Depends(get_db)):
    """List supported device classes (Milestone 1 taxonomy)."""
    classes = db.execute(
        select(DeviceClass).where(DeviceClass.supported.is_(True))
    ).scalars().all()
    return classes


@router.post("/assessments/analyze", response_model=AnalyzeResponse)
def analyze_assessment(
    image: UploadFile = File(..., description="Device photo (JPEG, PNG, WebP)"),
    age_years: int = Form(..., ge=0, le=50),
    powers_on: bool = Form(...),
    condition: str = Form(..., min_length=1, max_length=64),
    db: Session = Depends(get_db),
):
    """Run the full assessment pipeline for one uploaded device image."""
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{image.content_type}'. "
            "Upload a JPEG, PNG, or WebP image.",
        )
    image_bytes = image.file.read()
    max_bytes = settings.upload_max_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds the {settings.upload_max_mb} MB size limit.",
        )
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Classify
    try:
        ranked = get_classifier().analyze(image_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    top = ranked[0]

    # 2. Enrich from the curated knowledge base
    try:
        profile = get_profile(db, top.device_class)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # 3. Score + explain
    condition_facts = {
        "age_years": age_years,
        "powers_on": powers_on,
        "condition": condition,
    }
    result = recommend(profile, condition_facts)

    # 4. Persist the assessment (image bytes are discarded immediately)
    assessment = Assessment(
        device_class=top.device_class,
        age_years=age_years,
        powers_on=powers_on,
        condition=condition,
        image_deleted=True,
    )
    db.add(assessment)
    db.flush()
    db.add(
        Prediction(
            assessment_id=assessment.id,
            device_class=top.device_class,
            confidence=top.confidence,
            model_version=top.model_version,
        )
    )
    db.add(
        Recommendation(
            assessment_id=assessment.id,
            pathway=result.pathway,
            score=result.score,
            factors_json=json.dumps(result.factors),
            explanation_version=result.scoring_version,
            explanation=result.explanation,
        )
    )
    db.commit()

    return AnalyzeResponse(
        assessment_id=assessment.id,
        predicted_class=top.device_class,
        confidence=top.confidence,
        pathway=result.pathway,
        circularity_score=result.score,
        factors=result.factors,
        explanation=result.explanation,
        model_version=top.model_version,
        knowledge_version=profile.version,
        scoring_version=result.scoring_version,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Retrieve a previously completed assessment."""
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return AssessmentDetail(
        assessment_id=assessment.id,
        device_class=assessment.device_class,
        age_years=assessment.age_years,
        powers_on=assessment.powers_on,
        condition=assessment.condition,
        predicted_class=assessment.prediction.device_class if assessment.prediction else None,
        confidence=assessment.prediction.confidence if assessment.prediction else None,
        pathway=assessment.recommendation.pathway if assessment.recommendation else None,
        circularity_score=assessment.recommendation.score if assessment.recommendation else None,
    )
