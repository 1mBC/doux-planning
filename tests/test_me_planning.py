from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doux_planning.api.app import app
from doux_planning.api.db import reset_engine
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_me_planning_schema():
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


def _ready_patch(salle_id: str, cuisine_id: str) -> dict:
    return {
        "name": "Chez Test",
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
                "id": salle_id,
                "name": "Emma",
                "team": "salle",
                "role": {"name": "RESPONSABLE", "level": 3, "team": "salle"},
                "contractual_hours_per_week": 39,
                "wellbeing": {
                    "consecutive_rest": True,
                    "weekend_rest_day": True,
                    "weekend": None,
                    "max_services": {},
                    "max_coupures_per_week": None,
                },
                "unavailabilities": [{"weekday": "sunday", "service_id": "midday"}],
            },
            {
                "id": cuisine_id,
                "name": "Karim",
                "team": "cuisine",
                "role": {"name": "CHEF", "level": 4, "team": "cuisine"},
                "contractual_hours_per_week": 39,
            },
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


def test_me_planning_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    response = client.get("/v1/me/planning", headers=_bearer("x"))
    assert response.status_code == 503
    assert response.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_me_planning_published_grid_hides_live_draft():
    client = _client()
    email = f"me-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    company_token = registered.json()["token"]
    company_headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch(
        "/v1/context",
        headers=company_headers,
        json=_ready_patch(salle_id, cuisine_id),
    )
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]

    generated = client.post(
        "/v1/generate",
        headers=company_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    published = generated.json()["published"]["salle"]["assignments"]
    assert published
    cycles = client.get("/v1/cycles", headers=company_headers)
    assert cycles.status_code == 200
    assert cycles.json()["published"]["salle"]["assignments"] == published

    employee = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"emma-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": company_code,
            "employee_id": salle_id,
        },
    )
    assert employee.status_code == 201
    emp_headers = _bearer(employee.json()["token"])

    planning = client.get("/v1/me/planning", headers=emp_headers)
    assert planning.status_code == 200
    body = planning.json()
    assert body["employee_id"] == salle_id
    assert body["team"] == "salle"
    assert body["assignments"] == published
    assert all(shift["team"] == "salle" for shift in body["assignments"])
    assert {person["id"] for person in body["employees"]} == {salle_id}
    assert "invite_token" not in body
    assert all("invite_token" not in person for person in body["employees"])
    assert body["contract"]["weekly"] == 39
    assert "assigned" in body["contract"]
    assert isinstance(body["contract"]["ok"], bool)
    assert body["week_labels"] == "ab"
    assert body["wishes"]
    assert body["wishes"][0]["kind"] == "consecutive_rest"
    assert "key" not in body["wishes"][0]
    assert "held" in body["wishes"][0]
    rest_day = next(item for item in body["wishes"] if item["kind"] == "weekend_rest_day")
    assert "held" in rest_day
    assert "key" not in rest_day
    assert body["unavailabilities"] == [{"weekday": "sunday", "service_id": "midday"}]

    entered = client.post("/v1/live/sandbox/salle/enter", headers=company_headers)
    assert entered.status_code == 200
    shift = entered.json()["planning"]["assignments"][0]
    retune = {
        "gesture": "retune",
        "shift": {key: shift[key] for key in shift if key != "duration_hours"},
        "start_minutes": shift["start_minutes"] + 15,
        "end_minutes": shift["end_minutes"],
    }
    committed = client.post("/v1/live/sandbox/salle/commit", headers=company_headers, json=retune)
    assert committed.status_code == 200
    assert committed.json()["planning"]["assignments"] != published
    still = client.get("/v1/me/planning", headers=emp_headers)
    assert still.status_code == 200
    assert still.json()["assignments"] == published

    forbidden = client.get("/v1/me/planning", headers=company_headers)
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Action réservée au salarié."
    assert client.get("/v1/me/planning").status_code == 401

    cuisine = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"karim-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": company_code,
            "employee_id": cuisine_id,
        },
    )
    assert cuisine.status_code == 201
    empty = client.get("/v1/me/planning", headers=_bearer(cuisine.json()["token"]))
    assert empty.status_code == 200
    assert empty.json()["employee_id"] == cuisine_id
    assert empty.json()["team"] == "cuisine"
    assert empty.json()["assignments"] == []

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    login_token = logged.json()["token"]
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 200
    assert client.post("/v1/auth/logout", headers=_bearer(login_token)).status_code == 204
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 401
    assert client.get("/v1/cycles", headers=company_headers).status_code == 200
