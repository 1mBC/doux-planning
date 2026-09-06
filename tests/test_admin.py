from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, promote_admin_email
from doux_planning.api.db import GenerateLog, RestaurateurAccount, reset_engine, session_scope
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_admin_schema():
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


def _salle_patch(fiche_id: str, name: str = "Chez Admin") -> dict:
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


def _count_restaurateurs(email: str | None = None) -> int:
    with session_scope() as db:
        query = select(func.count()).select_from(RestaurateurAccount)
        if email is not None:
            query = query.where(RestaurateurAccount.email == email)
        return int(db.scalar(query) or 0)


def _clear_generate_logs() -> None:
    with session_scope() as db:
        for row in db.scalars(select(GenerateLog)):
            db.delete(row)


def _http_warning(item: dict) -> dict:
    return {
        "severity": item["severity"],
        "code": item["code"],
        "message": item["message"],
        "employee_id": item["employee_id"],
        "day_index": item["day_index"],
    }


def _assert_enriched_warnings(log_warnings: list, cycle_warnings: list, names: dict[str, str]) -> None:
    assert len(log_warnings) == len(cycle_warnings)
    for log_warning, cycle_warning in zip(log_warnings, cycle_warnings):
        assert _http_warning(log_warning) == cycle_warning
        employee_id = cycle_warning.get("employee_id")
        if employee_id:
            assert log_warning["employee_name"] == names.get(employee_id)
        else:
            assert log_warning["employee_name"] is None


def test_admin_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    listed = client.get("/v1/admin/generates", headers=_bearer("x"))
    assert listed.status_code == 503
    assert listed.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_promote_generate_logs_and_auth(monkeypatch):
    client = _client()
    password = "password1"
    email = f"admin-{secrets.token_hex(4)}@example.com"
    unknown = f"missing-{secrets.token_hex(4)}@example.com"
    before_unknown = _count_restaurateurs(unknown)
    before_all = _count_restaurateurs()

    monkeypatch.setenv("ADMIN_EMAIL", unknown)
    promote_admin_email()
    promote_admin_email()
    assert _count_restaurateurs(unknown) == before_unknown
    assert _count_restaurateurs() == before_all

    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    assert registered.json()["me"]["kind"] == "company"
    assert registered.json()["me"]["admin"] is False
    token = registered.json()["token"]
    headers = _bearer(token)
    assert client.get("/v1/me", headers=headers).json()["admin"] is False

    monkeypatch.setenv("ADMIN_EMAIL", f"  {email.upper()}  ")
    promote_admin_email()
    promote_admin_email()
    assert _count_restaurateurs(email) == 1
    mine = client.get("/v1/me", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["admin"] is True
    assert mine.json()["kind"] == "company"
    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    assert logged.json()["me"]["admin"] is True
    assert logged.json()["me"]["kind"] == "company"

    other = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"user-{secrets.token_hex(4)}@example.com", "password": password},
    )
    assert other.status_code == 201
    assert other.json()["me"]["admin"] is False
    other_headers = _bearer(other.json()["token"])
    forbidden_company = client.get("/v1/admin/generates", headers=other_headers)
    assert forbidden_company.status_code == 403
    assert forbidden_company.json()["detail"] == DETAIL_ADMIN

    _clear_generate_logs()
    empty = client.get("/v1/admin/generates", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {"entries": []}

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id, "Chez Admin"))
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]

    first = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert first.status_code == 200
    first_slot = first.json()["published"]["salle"]["versions"]["minimal"]
    assert first_slot["search_effort"] == "minimal"
    assert isinstance(first_slot["duration_seconds"], (int, float))
    assert first_slot["duration_seconds"] >= 0
    cycles = client.get("/v1/cycles", headers=headers)
    assert cycles.status_code == 200
    cycle_slot = cycles.json()["published"]["salle"]["versions"]["minimal"]
    assert isinstance(cycle_slot["duration_seconds"], (int, float))
    assert cycle_slot["duration_seconds"] >= 0
    after_one = client.get("/v1/admin/generates", headers=headers)
    assert after_one.status_code == 200
    assert len(after_one.json()["entries"]) == 1
    first_entry = after_one.json()["entries"][0]
    assert first_entry["email"] == email
    assert first_entry["restaurant_name"] == "Chez Admin"
    assert first_entry["team"] == "salle"
    assert first_entry["search_effort"] == "minimal"
    assert isinstance(first_entry["duration_seconds"], (int, float))
    assert first_entry["duration_seconds"] >= 0
    _assert_enriched_warnings(
        first_entry["warnings"],
        first_slot["warnings"],
        names={fiche_id: "Emma"},
    )
    assert "T" in first_entry["created_at"]

    cuisine = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "cuisine", "search_effort": "minimal"},
    )
    assert cuisine.status_code == 409
    still_one = client.get("/v1/admin/generates", headers=headers)
    assert still_one.status_code == 200
    assert len(still_one.json()["entries"]) == 1

    second = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert second.status_code == 200
    listed = client.get("/v1/admin/generates", headers=headers)
    assert listed.status_code == 200
    entries = listed.json()["entries"]
    assert len(entries) == 2
    assert entries[0]["created_at"] >= entries[1]["created_at"]
    assert entries[0]["id"] != first_entry["id"]
    assert entries[1]["id"] == first_entry["id"]
    assert entries[0]["search_effort"] == "minimal"
    assert isinstance(entries[0]["duration_seconds"], (int, float))
    assert entries[0]["duration_seconds"] >= 0
    _assert_enriched_warnings(
        entries[0]["warnings"],
        second.json()["published"]["salle"]["versions"]["minimal"]["warnings"],
        names={fiche_id: "Emma"},
    )

    old_id = f"legacy-{secrets.token_hex(4)}"
    with session_scope() as db:
        db.add(
            GenerateLog(
                id=old_id,
                created_at=datetime.now(timezone.utc) - timedelta(days=1),
                email="legacy@example.com",
                restaurant_name="Legacy",
                team="salle",
                search_effort=None,
                duration_seconds=None,
                warnings=[],
            )
        )
    with_legacy = client.get("/v1/admin/generates", headers=headers)
    assert with_legacy.status_code == 200
    legacy_entry = next(item for item in with_legacy.json()["entries"] if item["id"] == old_id)
    assert legacy_entry["search_effort"] is None
    assert legacy_entry["duration_seconds"] is None

    employee = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"emma-{secrets.token_hex(4)}@example.com",
            "password": password,
            "company_code": company_code,
            "employee_id": fiche_id,
        },
    )
    assert employee.status_code == 201
    assert employee.json()["me"]["admin"] is False
    assert employee.json()["me"]["kind"] == "employee"
    forbidden_emp = client.get("/v1/admin/generates", headers=_bearer(employee.json()["token"]))
    assert forbidden_emp.status_code == 403
    assert forbidden_emp.json()["detail"] == DETAIL_ADMIN
    assert client.get("/v1/admin/generates").status_code == 401

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
