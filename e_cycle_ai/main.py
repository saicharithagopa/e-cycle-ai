"""Application entry point: FastAPI app + minimal presentation layer."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from . import __version__
from .api.routes import router as api_router
from .seed import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="E-Cycle AI",
    description="Explainable e-waste circular-economy decision support (Milestone 2 starter).",
    version=__version__,
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health")
def health():
    """Liveness probe used by CI and deployment platforms."""
    return {"status": "ok", "version": __version__}


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>E-Cycle AI (Milestone 2)</title></head>
<body>
<h1>E-Cycle AI — Milestone 2 starter</h1>
<p>Upload a device photo plus condition facts to run the assessment pipeline.</p>
<form action="/api/v1/assessments/analyze" method="post" enctype="multipart/form-data">
  <label>Device photo: <input type="file" name="image" accept="image/*" required></label><br>
  <label>Age (years): <input type="number" name="age_years" min="0" max="50" value="4" required></label><br>
  <label>Powers on: <input type="checkbox" name="powers_on" value="true" checked></label><br>
  <label>Condition:
    <select name="condition">
      <option value="good">good</option>
      <option value="minor cosmetic damage">minor cosmetic damage</option>
      <option value="major damage">major damage</option>
    </select></label><br>
  <button type="submit">Analyze</button>
</form>
<p>API docs: <a href="/docs">/docs</a> · Health: <a href="/health">/health</a></p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    """Minimal server-rendered upload form (presentation layer placeholder)."""
    return _INDEX_HTML
