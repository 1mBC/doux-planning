from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, promote_admin_email
from doux_planning.api.bench import DETAIL_BENCH_MISSING
from doux_planning.api.db import (
    BenchImportedDataset,
    BenchJob,
    BenchRun,
    BenchTombstone,
    reset_engine,
    session_scope,
)
from doux_planning.bench import bench_dir
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_chrome_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def _open_week(type_id: str | None) -> list[dict]:
    return [
        {
            "weekday": day,
            "service_id": "midday",
            "type_id": type_id,
            "closed": False,
        }
        for day in WEEKDAYS
    ]


def _salle_patch(fiche_id: str, name: str) -> dict:
    return {
        "name": name,
        "services": ["midday"],
        "ladders": {
            "salle": {
                "roles": [{"name": "RESPONSABLE", "level": 3}, {"name": "EQUIPIER", "level": 1}],
                "substitution_explained": True,
            },
            "cuisine": None,
        },
        "employees": [
            {
                "id": fiche_id,
                "name": "Emma",
                "team": "salle",
                "role": {"name": "RESPONSABLE", "level": 3, "team": "salle"},
                "contractual_hours_per_week": 39,
            }
        ],
        "types": [
            {
                "id": "salle-midi",
                "name": "Salle midi",
                "team": "salle",
                "service_id": "midday",
                "arrivals": [{"time_minutes": 11 * 60, "post_levels": [1]}],
                "departures": [{"time_minutes": 16 * 60, "remaining_post_levels": []}],
            }
        ],
        "typical_week": {"salle": _open_week("salle-midi"), "cuisine": None},
    }


def _register_company(client: TestClient, email: str, password: str = "password1") -> tuple[str, str]:
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    assert isinstance(restaurant_id, str)
    return token, restaurant_id


def _promote(client: TestClient, email: str, token: str, monkeypatch) -> dict[str, str]:
    monkeypatch.setenv("ADMIN_EMAIL", email)
    promote_admin_email()
    headers = _bearer(token)
    assert client.get("/v1/me", headers=headers).json()["admin"] is True
    return headers


def _pair_counts(category: str, dataset_id: str) -> tuple[int, int]:
    with session_scope() as db:
        runs = db.scalar(
            select(func.count())
            .select_from(BenchRun)
            .where(BenchRun.category == category, BenchRun.dataset_id == dataset_id)
        )
        jobs = db.scalar(
            select(func.count())
            .select_from(BenchJob)
            .where(BenchJob.category == category, BenchJob.dataset_id == dataset_id)
        )
    return int(runs or 0), int(jobs or 0)


def _clear_halles_tombstone() -> None:
    with session_scope() as db:
        row = db.get(BenchTombstone, ("tight", "halles"))
        if row is not None:
            db.delete(row)


def _versions_ids(client: TestClient, headers: dict[str, str]) -> set[tuple[str, str]]:
    versions = client.get("/v1/admin/bench/versions", headers=headers)
    assert versions.status_code == 200
    return {(item["category"], item["id"]) for item in versions.json()["datasets"]}


def test_bench_delete_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    deleted = client.delete("/v1/admin/bench/datasets/tight/halles", headers=_bearer("x"))
    assert deleted.status_code == 503
    assert deleted.json()["detail"] == "Base indisponible."


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_delete_bench_dataset_imported_catalogue_and_auth(monkeypatch):
    client = _client()
    password = "password1"
    admin_email = f"chrome-admin-{secrets.token_hex(4)}@example.com"
    resto_email = f"chrome-resto-{secrets.token_hex(4)}@example.com"
    admin_token, _admin_rid = _register_company(client, admin_email, password)
    admin_headers = _promote(client, admin_email, admin_token, monkeypatch)
    other_token, restaurant_id = _register_company(client, resto_email, password)
    other_headers = _bearer(other_token)

    forbidden = client.delete("/v1/admin/bench/datasets/tight/halles", headers=other_headers)
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == DETAIL_ADMIN
    unauth = client.delete("/v1/admin/bench/datasets/tight/halles")
    assert unauth.status_code == 401

    missing = client.delete("/v1/admin/bench/datasets/tight/unknown-jeu-xyz", headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == DETAIL_BENCH_MISSING

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=other_headers, json=_salle_patch(fiche_id, "Chez Chrome"))
    assert patched.status_code == 200
    generated = client.post(
        "/v1/generate",
        headers=other_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    imported = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": restaurant_id, "include_runs": True, "comment": "a dropper"},
    )
    assert imported.status_code == 200
    imported_id = imported.json()["id"]
    queued = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={
            "scope": "dataset",
            "category": "imported",
            "dataset_id": imported_id,
            "search_effort": "maximal",
        },
    )
    assert queued.status_code == 202
    assert queued.json()["job_ids"]
    assert ("imported", imported_id) in _versions_ids(client, admin_headers)
    assert _pair_counts("imported", imported_id)[0] >= 1
    assert _pair_counts("imported", imported_id)[1] >= 1

    dropped = client.delete(f"/v1/admin/bench/datasets/imported/{imported_id}", headers=admin_headers)
    assert dropped.status_code == 204
    assert dropped.content == b""
    assert ("imported", imported_id) not in _versions_ids(client, admin_headers)
    assert _pair_counts("imported", imported_id) == (0, 0)
    with session_scope() as db:
        assert db.get(BenchImportedDataset, imported_id) is None
    again_imported = client.delete(f"/v1/admin/bench/datasets/imported/{imported_id}", headers=admin_headers)
    assert again_imported.status_code == 404
    assert again_imported.json()["detail"] == DETAIL_BENCH_MISSING

    halles_dir = bench_dir() / "tight" / "halles"
    try:
        first = client.delete("/v1/admin/bench/datasets/tight/halles", headers=admin_headers)
        assert first.status_code == 204
        listed = _versions_ids(client, admin_headers)
        assert ("tight", "halles") not in listed
        datasets = client.get("/v1/admin/bench/datasets", headers=admin_headers)
        assert datasets.status_code == 200
        assert all(not (item["category"] == "tight" and item["id"] == "halles") for item in datasets.json()["datasets"])
        assert halles_dir.is_dir()
        assert (halles_dir / "context.json").is_file()
        assert (halles_dir / "expected.json").is_file()
        assert _pair_counts("tight", "halles") == (0, 0)
        second = client.delete("/v1/admin/bench/datasets/tight/halles", headers=admin_headers)
        assert second.status_code == 204
        gaps = client.post("/v1/admin/bench/run", headers=admin_headers, json={"scope": "gaps"})
        assert gaps.status_code in (200, 202)
        job_ids = gaps.json()["job_ids"]
        if job_ids:
            with session_scope() as db:
                batch_jobs = list(db.scalars(select(BenchJob).where(BenchJob.id.in_(job_ids))))
            assert all(not (job.category == "tight" and job.dataset_id == "halles") for job in batch_jobs)
        assert _pair_counts("tight", "halles") == (0, 0)
        with session_scope() as db:
            for job in db.scalars(select(BenchJob).where(BenchJob.status.in_(("queued", "running")))):
                if job.batch_id == gaps.json().get("batch_id"):
                    job.status = "failed"
                    job.error = "test cleanup"
    finally:
        _clear_halles_tombstone()
    restored = _versions_ids(client, admin_headers)
    assert ("tight", "halles") in restored
