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
def _postgres_live_schema():
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


def _salle_patch(fiche_id: str, name: str = "Chez Test") -> dict:
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


def _retune_body(shift: dict, start: int, end: int) -> dict:
    payload = {key: shift[key] for key in shift if key != "duration_hours"}
    return {
        "gesture": "retune",
        "shift": payload,
        "start_minutes": start,
        "end_minutes": end,
    }


def test_live_sandbox_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    headers = _bearer("x")
    enter = client.post("/v1/live/sandbox/salle/enter", headers=headers)
    assert enter.status_code == 503
    assert enter.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert client.post("/v1/sandbox/enter").status_code == 200


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_live_sandbox_enter_edit_publish_and_joujou():
    client = _client()
    email = f"live-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]

    generated = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    original = generated.json()["published"]["salle"]["assignments"]
    assert original

    missing = client.get("/v1/live/sandbox/salle", headers=headers)
    assert missing.status_code == 404

    entered = client.post("/v1/live/sandbox/salle/enter", headers=headers)
    assert entered.status_code == 200
    body = entered.json()
    assert body["team"] == "salle"
    assert body["planning"]["assignments"]
    assert body["history"] == []
    assert all(person["team"] == "salle" for person in body["restaurant"]["employees"])

    cuisine = client.post("/v1/live/sandbox/cuisine/enter", headers=headers)
    assert cuisine.status_code == 409
    assert cuisine.json()["detail"] == "Aucun cycle publié pour cette équipe."

    invalid = client.post("/v1/live/sandbox/bar/enter", headers=headers)
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Champs invalides."

    shift = body["planning"]["assignments"][0]
    retune = _retune_body(shift, shift["start_minutes"] + 15, shift["end_minutes"])
    preview = client.post("/v1/live/sandbox/salle/preview", headers=headers, json=retune)
    assert preview.status_code == 200
    assert preview.json()["proposals"]
    assert preview.json()["proposals"][0]["gesture"] == "retune"

    committed = client.post("/v1/live/sandbox/salle/commit", headers=headers, json=retune)
    assert committed.status_code == 200
    changed = committed.json()["planning"]["assignments"]
    assert changed != original
    assert committed.json()["history"]

    undone = client.post("/v1/live/sandbox/salle/undo", headers=headers)
    assert undone.status_code == 200
    assert undone.json()["planning"]["assignments"] == original
    assert undone.json()["history"] == []

    committed_again = client.post("/v1/live/sandbox/salle/commit", headers=headers, json=retune)
    assert committed_again.status_code == 200
    discarded = client.post("/v1/live/sandbox/salle/discard", headers=headers)
    assert discarded.status_code == 200
    assert discarded.json()["planning"]["assignments"] == original
    assert discarded.json()["history"] == []

    reentered = client.post("/v1/live/sandbox/salle/enter", headers=headers)
    assert reentered.status_code == 200
    opened = client.post("/v1/live/sandbox/salle/commit", headers=headers, json=retune)
    assert opened.status_code == 200
    open_body = opened.json()
    reset_engine()
    restored = client.get("/v1/live/sandbox/salle", headers=headers)
    assert restored.status_code == 200
    assert restored.json()["planning"]["assignments"] == open_body["planning"]["assignments"]
    assert restored.json()["history"] == open_body["history"]

    published = client.post("/v1/live/sandbox/salle/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["published"]["salle"]["assignments"] == open_body["planning"]["assignments"]
    assert published.json()["published"]["cuisine"] is None
    cycles = client.get("/v1/cycles", headers=headers)
    assert cycles.status_code == 200
    assert cycles.json()["published"]["salle"]["assignments"] != original
    assert cycles.json()["published"]["cuisine"] is None
    closed = client.get("/v1/live/sandbox/salle", headers=headers)
    assert closed.status_code == 404

    employee = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"emma-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": company_code,
            "employee_id": fiche_id,
        },
    )
    assert employee.status_code == 201
    forbidden = client.post(
        "/v1/live/sandbox/salle/enter",
        headers=_bearer(employee.json()["token"]),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Action réservée au restaurateur."

    assert client.post("/v1/sandbox/enter").status_code == 200
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
