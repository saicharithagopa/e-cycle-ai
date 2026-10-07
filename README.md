# E-Cycle AI

Explainable e-waste circular-economy decision support — a Python web app that
photographs an e-device, identifies it with AI, and recommends
**Repair / Reuse / Recycle** with an explainable Circularity Score.

**CS 690 · Software Development Project · Group 2** (Milestone 2 starter code)

| Member | Roles |
|---|---|
| Sai Charitha | Project Manager / Scrum Master · Backend & AI Lead |
| Tejesh | Frontend & UX Lead · QA / DevOps Lead |


## Quickstart (local development)

**Prerequisites:** Python 3.12+, `pip`, Git. Optional: Docker.

```bash
# 1. Clone
git clone https://github.com/saicharithagopa/e-cycle-ai.git e-cycle-ai
cd e-cycle-ai

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) run database migrations instead of auto-create
# alembic upgrade head

# 5. Start the app (tables + seed data are created on startup)
uvicorn e_cycle_ai.main:app --reload

# 6. Verify it works: open http://127.0.0.1:8000/health
#    You should see: {"status": "ok", "version": "0.2.0"}
```

Open **http://127.0.0.1:8000** for the upload form and
**http://127.0.0.1:8000/docs** for the interactive API docs.

**Environment variables** (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./e_cycle_ai.db` | Database connection string |
| `UPLOAD_MAX_MB` | `10` | Max upload size |
| `IMAGE_RETENTION_HOURS` | `24` | Documented retention window (images are never persisted) |

## Run the tests

```bash
pytest -q
```

## Run with Docker

```bash
docker build -t e-cycle-ai .
docker run -p 8000:8000 e-cycle-ai
```

## Project structure

```
e_cycle_ai/
  main.py            # FastAPI app + minimal presentation layer (upload form)
  config.py          # Environment-driven settings
  db.py              # SQLAlchemy engine / sessions
  models.py          # ORM: DeviceClass, DeviceProfile, ScoringRule,
                     #        Assessment, Prediction, Recommendation
  schemas.py         # Pydantic request/response contracts
  seed.py            # Idempotent seed: taxonomy, laptop profile, scoring rules
  classifier/        # base.py = interface contract; stub.py = deterministic stub
                     # (swap in the trained torchvision model in Milestone 3)
  knowledge/         # service.py: versioned curated profile lookup
  decision/          # engine.py: versioned weighted scoring + explanations
  api/routes.py      # REST routes: validate -> classify -> enrich -> score -> explain
alembic/             # Database migrations (versions/0001_initial.py)
tests/               # pytest: decision-engine units + API integration tests
.github/workflows/  # CI: install -> compile check -> pytest -> migration check
```

## API overview

| Method & route | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `GET /` | Minimal upload form (presentation placeholder) |
| `GET /api/v1/device-classes` | Supported device taxonomy |
| `POST /api/v1/assessments/analyze` | Full pipeline: image + `age_years`, `powers_on`, `condition` |
| `GET /api/v1/assessments/{id}` | Retrieve a completed assessment |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/assessments/analyze \
  -F "image=@laptop.jpg" -F "age_years=4" -F "powers_on=true" -F "condition=good"
```

## Version control strategy

- **Branches:** `main` (protected, always releasable), `develop` (integration),
  `feature/<short-name>` and `fix/<short-name>` for all work.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`),
  one logical change per commit, present tense.
- **Reviews:** every change merges via pull request into `develop` with at least
  one peer approval; CI must pass before merge. `main` is updated from `develop`
  at milestone boundaries via a release PR reviewed by both members.

## Continuous integration

On every push and pull request, GitHub Actions runs:

1. Install dependencies (Python 3.12)
2. `python -m compileall` — compile check
3. `pytest -q` — full test suite
4. `alembic upgrade head && alembic downgrade base` — migration chain check
