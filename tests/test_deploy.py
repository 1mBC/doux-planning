from __future__ import annotations

from fastapi.testclient import TestClient

from doux_planning.api.app import app, web_dist
from doux_planning.api.db import normalize_database_url


def _client() -> TestClient:
    return TestClient(app)


def test_example_without_dist_is_92():
    client = _client()
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert example.headers.get("content-type", "").startswith("application/json")


def test_postgres_url_normalizes_to_psycopg():
    assert (
        normalize_database_url("postgres://doux:doux@db:5432/doux_planning")
        == "postgresql+psycopg://doux:doux@db:5432/doux_planning"
    )
    assert (
        normalize_database_url("postgresql://doux:doux@db:5432/doux_planning")
        == "postgresql+psycopg://doux:doux@db:5432/doux_planning"
    )
    already = "postgresql+psycopg://doux:doux@localhost:5432/doux_planning"
    assert normalize_database_url(already) == already


def test_dual_read_without_database_url(monkeypatch):
    from doux_planning.api.db import reset_engine

    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    auth = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": "nodb@example.com", "password": "password1"},
    )
    assert auth.status_code == 503
    assert auth.json()["detail"] == "Base indisponible."


def test_spa_planning_serves_index_when_dist_exists():
    dist = web_dist()
    if dist is None:
        import pytest

        pytest.skip("web/dist absent")
    index = (dist / "index.html").read_text(encoding="utf-8")
    client = _client()
    page = client.get("/planning")
    assert page.status_code == 200
    assert "<html" in page.text.lower()
    assert page.text == index
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
