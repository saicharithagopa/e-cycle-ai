"""Deterministic, versioned decision engine.

Interface: recommend(profile, condition) -> RecommendationResult, where
condition = {"age_years": int, "powers_on": bool, "condition": str}.

The Circularity Score is a normalized decision aid (0-100), not a physical
measurement. Four factor scores (each 0..1) are combined with versioned
weights; every output carries the scoring version so results stay traceable.
Ties between pathways resolve deterministically toward repair.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..knowledge.service import DeviceProfileData

SCORING_VERSION = "0.2.0"

# Versioned factor weights — must sum to 1.0. Calibrated in Milestone 3.
FACTOR_WEIGHTS: dict[str, float] = {
    "repairability": 0.30,
    "reuse": 0.30,
    "recyclability": 0.20,
    "recovery": 0.20,
}

assert abs(sum(FACTOR_WEIGHTS.values()) - 1.0) < 1e-9, "factor weights must sum to 1.0"


@dataclass(frozen=True)
class RecommendationResult:
    pathway: str  # "repair" | "reuse" | "recycle"
    score: float  # 0..100
    factors: dict[str, float]
    explanation: str
    scoring_version: str = SCORING_VERSION


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_factors(condition: dict) -> dict[str, float]:
    """Compute the four factor scores from user-supplied condition facts."""
    age = int(condition.get("age_years", 0))
    powers_on = bool(condition.get("powers_on", False))
    cond = str(condition.get("condition", "unknown")).lower()

    repairability = 0.70 if powers_on else 0.25
    reuse = 0.80 if powers_on else 0.15
    recyclability = 0.60
    recovery = 0.55

    if age <= 3:
        repairability += 0.10
        reuse += 0.10
    elif age > 6:
        repairability -= 0.15
        reuse -= 0.15

    if "good" in cond or "excellent" in cond:
        repairability += 0.10
        reuse += 0.10
    elif "major" in cond or "broken" in cond or "severe" in cond:
        # Significant damage hurts repair/reuse prospects and pushes
        # the device toward responsible recycling. Minor cosmetic wear
        # ("minor cosmetic damage", "fair") is treated as neutral.
        repairability -= 0.20
        reuse -= 0.20
        recyclability += 0.20

    return {
        "repairability": round(_clamp01(repairability), 3),
        "reuse": round(_clamp01(reuse), 3),
        "recyclability": round(_clamp01(recyclability), 3),
        "recovery": round(_clamp01(recovery), 3),
    }


def _choose_pathway(factors: dict[str, float]) -> str:
    best_value = max(factors["repairability"], factors["reuse"], factors["recyclability"])
    if factors["recyclability"] >= best_value and factors["recyclability"] > max(
        factors["repairability"], factors["reuse"]
    ):
        return "recycle"
    # Deterministic tie-break: repair wins ties (preserve functional value first).
    if factors["repairability"] >= factors["reuse"]:
        return "repair"
    return "reuse"


def recommend(profile: DeviceProfileData, condition: dict) -> RecommendationResult:
    """Rank repair / reuse / recycle and explain the result."""
    factors = score_factors(condition)
    score = round(
        sum(factors[f] * w for f, w in FACTOR_WEIGHTS.items()) * 100, 1
    )
    pathway = _choose_pathway(factors)

    hazards = ", ".join(profile.hazards) if profile.hazards else "none listed"
    explanation = (
        f"Recommended pathway: {pathway.upper()} (Circularity Score {score}/100). "
        f"Repairability {factors['repairability']}, reuse potential {factors['reuse']}, "
        f"recyclability {factors['recyclability']}, material recovery {factors['recovery']}. "
        f"Based on the curated '{profile.device_class}' profile (v{profile.version}); "
        f"material values are category-level estimates, not measurements of this unit. "
        f"Handling notes: {hazards}. {profile.caveats}"
    ).strip()
    return RecommendationResult(
        pathway=pathway, score=score, factors=factors, explanation=explanation
    )
