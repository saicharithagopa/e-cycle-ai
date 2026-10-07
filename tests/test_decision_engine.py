"""Unit tests for the rule-based decision engine (Milestone 1 NFR-01, NFR-06)."""

from __future__ import annotations

from e_cycle_ai.decision.engine import (
    FACTOR_WEIGHTS,
    SCORING_VERSION,
    recommend,
    score_factors,
)
from e_cycle_ai.knowledge.service import DeviceProfileData


def _profile() -> DeviceProfileData:
    return DeviceProfileData(
        device_class="laptop",
        version="0.2.0",
        components=[],
        materials=[],
        hazards=["Lithium-ion battery: do not puncture."],
        caveats="Category-level estimates only.",
    )


def test_factor_weights_sum_to_one():
    assert abs(sum(FACTOR_WEIGHTS.values()) - 1.0) < 1e-9


def test_score_is_bounded_0_to_100():
    healthy = {"age_years": 1, "powers_on": True, "condition": "good"}
    broken = {"age_years": 12, "powers_on": False, "condition": "major damage"}
    for cond in (healthy, broken):
        result = recommend(_profile(), cond)
        assert 0.0 <= result.score <= 100.0
        assert result.scoring_version == SCORING_VERSION


def test_healthy_laptop_prefers_repair_or_reuse():
    result = recommend(
        _profile(), {"age_years": 2, "powers_on": True, "condition": "good"}
    )
    assert result.pathway in ("repair", "reuse")
    assert result.score > 60


def test_dead_heavily_damaged_device_is_recycled():
    result = recommend(
        _profile(),
        {"age_years": 10, "powers_on": False, "condition": "major damage"},
    )
    assert result.pathway == "recycle"


def test_tie_break_is_deterministic_toward_repair():
    # Identical inputs must always resolve to the same pathway.
    cond = {"age_years": 5, "powers_on": True, "condition": "minor cosmetic damage"}
    first = recommend(_profile(), cond).pathway
    for _ in range(5):
        assert recommend(_profile(), cond).pathway == first


def test_explanation_states_limitations():
    result = recommend(
        _profile(), {"age_years": 4, "powers_on": True, "condition": "good"}
    )
    assert "estimates" in result.explanation.lower()
    assert "0.2.0" in result.explanation or "v0.2.0" in result.explanation


def test_all_four_factors_present():
    factors = score_factors({"age_years": 4, "powers_on": True, "condition": "good"})
    assert set(factors) == {"repairability", "reuse", "recyclability", "recovery"}
    assert all(0.0 <= v <= 1.0 for v in factors.values())
