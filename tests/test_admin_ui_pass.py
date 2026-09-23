from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, DETAIL_INVALID_FIELDS, promote_admin_email
from doux_planning.api.db import BenchJob, reset_engine, session_scope
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_admin_ui_pass_schema():
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


def _jobs(job_ids: list[str]) -> list[BenchJob]:
    if not job_ids:
        return []
    with session_scope() as db:
        return list(db.scalars(select(BenchJob).where(BenchJob.id.in_(job_ids))))


def test_spa_admin_bench_manuels_serves_index():
    from doux_planning.api.app import web_dist

    dist = web_dist()
    if dist is None:
        pytest.skip("web/dist absent")
    index = (dist / "index.html").read_text(encoding="utf-8")
    page = _client().get("/admin/bench/manuels")
    assert page.status_code == 200
    assert page.text == index


def test_spa_admin_bench_manuels_mounts_index(tmp_path, monkeypatch):
    from fastapi import FastAPI

    from doux_planning.api import app as app_mod

    dist = tmp_path / "dist"
    dist.mkdir()
    index = dist / "index.html"
    index.write_text("<html><body>spa-manuels</body></html>", encoding="utf-8")
    monkeypatch.setattr(app_mod, "web_dist", lambda: dist)
    application = FastAPI()
    app_mod._mount_spa(application)
    client = TestClient(application)
    page = client.get("/admin/bench/manuels")
    assert page.status_code == 200
    assert page.text == index.read_text(encoding="utf-8")
    same = client.get("/admin/bench")
    assert same.status_code == 200
    assert same.text == page.text


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_bench_run_and_export_origin_filter(monkeypatch):
    client = _client()
    password = "password1"
    admin_email = f"uipass-admin-{secrets.token_hex(4)}@example.com"
    resto_email = f"uipass-resto-{secrets.token_hex(4)}@example.com"
    admin_token, _admin_rid = _register_company(client, admin_email, password)
    admin_headers = _promote(client, admin_email, admin_token, monkeypatch)
    other_token, restaurant_id = _register_company(client, resto_email, password)
    other_headers = _bearer(other_token)

    nope_run = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "all", "search_effort": "maximal", "origin": "nope"},
    )
    assert nope_run.status_code == 400
    assert nope_run.json()["detail"] == DETAIL_INVALID_FIELDS
    nope_gaps = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "gaps", "origin": "nope"},
    )
    assert nope_gaps.status_code == 400
    assert nope_gaps.json()["detail"] == DETAIL_INVALID_FIELDS
    nope_export = client.get(
        "/v1/admin/bench/export",
        headers=admin_headers,
        params={"scope": "bank", "origin": "nope"},
    )
    assert nope_export.status_code == 400
    assert nope_export.json()["detail"] == DETAIL_INVALID_FIELDS

    forbidden_run = client.post(
        "/v1/admin/bench/run",
        headers=other_headers,
        json={"scope": "all", "search_effort": "maximal", "origin": "catalogue"},
    )
    assert forbidden_run.status_code == 403
    assert forbidden_run.json()["detail"] == DETAIL_ADMIN
    forbidden_export = client.get(
        "/v1/admin/bench/export",
        headers=other_headers,
        params={"scope": "bank", "origin": "catalogue"},
    )
    assert forbidden_export.status_code == 403
    assert forbidden_export.json()["detail"] == DETAIL_ADMIN

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=other_headers, json=_salle_patch(fiche_id, "Chez Manuels"))
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
        json={"restaurant_id": restaurant_id, "include_runs": True, "comment": "manuels"},
    )
    assert imported.status_code == 200
    imported_id = imported.json()["id"]
    assert imported.json()["category"] == "imported"

    catalogue_all = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "all", "search_effort": "maximal", "origin": "catalogue"},
    )
    assert catalogue_all.status_code == 202
    catalogue_jobs = _jobs(catalogue_all.json()["job_ids"])
    assert catalogue_jobs
    assert all(job.category != "imported" for job in catalogue_jobs)
    assert imported_id not in {job.dataset_id for job in catalogue_jobs}

    imported_all = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "all", "search_effort": "maximal", "origin": "imported"},
    )
    assert imported_all.status_code == 202
    imported_jobs = _jobs(imported_all.json()["job_ids"])
    assert imported_jobs
    assert all(job.category == "imported" for job in imported_jobs)
    assert imported_id in {job.dataset_id for job in imported_jobs}

    catalogue_gaps = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "gaps", "origin": "catalogue"},
    )
    assert catalogue_gaps.status_code in (200, 202)
    gap_jobs = _jobs(catalogue_gaps.json()["job_ids"])
    assert all(job.category != "imported" for job in gap_jobs)
    assert imported_id not in {job.dataset_id for job in gap_jobs}

    both_all = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "all", "search_effort": "maximal"},
    )
    assert both_all.status_code == 202
    both_jobs = _jobs(both_all.json()["job_ids"])
    both_cats = {job.category for job in both_jobs}
    assert "imported" in both_cats
    assert any(category != "imported" for category in both_cats)
    assert imported_id in {job.dataset_id for job in both_jobs}

    both_gaps = client.post("/v1/admin/bench/run", headers=admin_headers, json={"scope": "gaps"})
    assert both_gaps.status_code in (200, 202)
    both_gap_jobs = _jobs(both_gaps.json()["job_ids"])
    assert any(job.category == "imported" for job in both_gap_jobs)
    assert any(job.category != "imported" for job in both_gap_jobs)

    empty_mismatch = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={
            "scope": "category",
            "category": "imported",
            "search_effort": "maximal",
            "origin": "catalogue",
        },
    )
    assert empty_mismatch.status_code == 202
    assert empty_mismatch.json()["total"] == 0
    assert empty_mismatch.json()["job_ids"] == []

    bank = client.get(
        "/v1/admin/bench/export",
        headers=admin_headers,
        params={"scope": "bank", "origin": "catalogue"},
    )
    assert bank.status_code == 200
    assert all(item["category"] != "imported" for item in bank.json()["datasets"])
    assert imported_id not in {item["id"] for item in bank.json()["datasets"]}
