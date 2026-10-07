"""Test fixtures: in-memory SQLite + FastAPI TestClient with seeded data."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from e_cycle_ai.db import Base, get_db
from e_cycle_ai.main import app
from e_cycle_ai.seed import seed_db

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(
    bind=_test_engine, autoflush=False, autocommit=False
)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=_test_engine)
    session = _TestingSessionLocal()
    seed_db(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
