"""API integration tests: full pipeline via the HTTP layer."""

from __future__ import annotations

import io

from PIL import Image


def _png_bytes(color: str = "red") -> bytes:
    img = Image.new("RGB", (64, 64), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _analyze(client, **overrides):
    data = {
        "age_years": "4",
        "powers_on": "true",
        "condition": "good",
        **overrides,
    }
    files = {"image": ("photo.png", _png_bytes(), "image/png")}
    return client.post("/api/v1/assessments/analyze", files=files, data=data)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_device_classes_lists_supported_taxonomy(client):
    resp = client.get("/api/v1/device-classes")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert {"laptop", "phone", "tablet"} <= names


def test_analyze_happy_path_returns_full_pipeline_result(client):
    resp = _analyze(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_class"] == "laptop"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["pathway"] in ("repair", "reuse", "recycle")
    assert 0.0 <= body["circularity_score"] <= 100.0
    assert set(body["factors"]) == {
        "repairability",
        "reuse",
        "recyclability",
        "recovery",
    }
    assert body["model_version"]
    assert body["knowledge_version"]
    assert body["scoring_version"]


def test_analyze_rejects_non_image_upload(client):
    resp = client.post(
        "/api/v1/assessments/analyze",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
        data={"age_years": "4", "powers_on": "true", "condition": "good"},
    )
    assert resp.status_code == 400


def test_get_assessment_round_trip(client):
    created = _analyze(client).json()
    resp = client.get(f"/api/v1/assessments/{created['assessment_id']}")
    assert resp.status_code == 200
    assert resp.json()["pathway"] == created["pathway"]


def test_get_assessment_404(client):
    resp = client.get("/api/v1/assessments/999999")
    assert resp.status_code == 404
