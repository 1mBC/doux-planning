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
def _postgres_context_schema():
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


def test_context_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    response = client.get("/v1/context", headers=_bearer("x"))
    assert response.status_code == 503
    assert response.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert client.post("/v1/sandbox/enter").status_code == 200


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_context_get_patch_ready_invites_and_auth():
    client = _client()
    email = f"ctx-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    assert restaurant_id != "saint-cloud"

    empty = client.get("/v1/context", headers=_bearer(token))
    assert empty.status_code == 200
    body = empty.json()
    assert body["name"] == ""
    assert body["legal_context_id"] == "france"
    assert body["company_code"]
    assert body["services"] == []
    assert body["ladders"] == {"salle": None, "cuisine": None}
    assert body["employees"] == []
    assert body["types"] == []
    assert body["typical_week"] == {"salle": None, "cuisine": None}
    assert body["ready"] == {"salle": False, "cuisine": False}
    assert body["week_labels"] == "ab"

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=_bearer(token), json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    ready = patched.json()
    assert ready["name"] == "Chez Test"
    assert ready["ready"]["salle"] is True
    assert ready["ready"]["cuisine"] is False
    assert ready["employees"][0]["id"] == fiche_id
    assert ready["employees"][0]["invite_token"]
    assert ready["employees"][0]["min_shift_hours"] == 4
    assert ready["week_labels"] == "ab"
    assert ready["employees"][0]["wellbeing"] == {
        "consecutive_rest": False,
        "weekend": None,
        "max_services": {},
        "max_coupures_per_week": None,
    }
    company_code = ready["company_code"]

    reset_engine()
    again = client.get("/v1/context", headers=_bearer(token))
    assert again.status_code == 200
    assert again.json() == ready

    invites = client.get(f"/v1/invites/{company_code}")
    assert invites.status_code == 200
    people = invites.json()["employees"]
    assert {person["id"] for person in people} == {fiche_id}
    assert people[0]["role"] == "RESPONSABLE"
    assert "invite_token" not in people[0]

    open_without_type = client.patch(
        "/v1/context",
        headers=_bearer(token),
        json={"typical_week": {"salle": _open_week(None), "cuisine": None}},
    )
    assert open_without_type.status_code == 200
    assert open_without_type.json()["ready"]["salle"] is False
    assert open_without_type.json()["ready"]["cuisine"] is False

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
    forbidden = client.get("/v1/context", headers=_bearer(employee.json()["token"]))
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Action réservée au restaurateur."
    forbidden_patch = client.patch(
        "/v1/context",
        headers=_bearer(employee.json()["token"]),
        json={"name": "Nope"},
    )
    assert forbidden_patch.status_code == 403

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    with_session = client.get("/v1/examples/saint-cloud", headers=_bearer(token))
    assert with_session.status_code == 200
    assert with_session.json()["planning"]["stats"]["assignments"] == 92

    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    login_token = logged.json()["token"]
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 200
    assert client.post("/v1/auth/logout", headers=_bearer(login_token)).status_code == 204
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 401


def _fiche_payload(fiche_id: str, *, weekend: str | None, unavailabilities: list | None = None) -> dict:
    return {
        "id": fiche_id,
        "name": "Emma",
        "team": "salle",
        "role": {"name": "RESPONSABLE", "level": 3, "team": "salle"},
        "contractual_hours_per_week": 39,
        "wellbeing": {
            "consecutive_rest": False,
            "weekend": weekend,
            "max_services": {},
            "max_coupures_per_week": None,
        },
        "unavailabilities": unavailabilities or [],
    }


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_context_wellbeing_week_labels_and_unavail_service_id():
    client = _client()
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"wb-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    fiche_id = f"emma-{secrets.token_hex(4)}"

    even = client.patch(
        "/v1/context",
        headers=headers,
        json={"employees": [_fiche_payload(fiche_id, weekend="even")]},
    )
    assert even.status_code == 200
    assert even.json()["week_labels"] == "parity"
    assert even.json()["employees"][0]["wellbeing"]["weekend"] == "even"
    assert even.json()["employees"][0]["unavailabilities"] == []

    reset_engine()
    again = client.get("/v1/context", headers=headers)
    assert again.status_code == 200
    assert again.json()["week_labels"] == "parity"
    assert again.json()["employees"][0]["wellbeing"] == {
        "consecutive_rest": False,
        "weekend": "even",
        "max_services": {},
        "max_coupures_per_week": None,
    }

    two = client.patch(
        "/v1/context",
        headers=headers,
        json={"employees": [_fiche_payload(fiche_id, weekend="every_two")]},
    )
    assert two.status_code == 200
    assert two.json()["week_labels"] == "ab"
    assert two.json()["employees"][0]["wellbeing"]["weekend"] == "every_two"

    missing = client.patch(
        "/v1/context",
        headers=headers,
        json={"employees": [_fiche_payload(fiche_id, weekend="every_two", unavailabilities=[{"weekday": "sunday"}])]},
    )
    assert missing.status_code == 400
    assert missing.json()["detail"] == "Champs invalides."
    still = client.get("/v1/context", headers=headers)
    assert still.status_code == 200
    assert still.json()["week_labels"] == "ab"
    assert still.json()["employees"][0]["unavailabilities"] == []

    forced = client.patch("/v1/context", headers=headers, json={"week_labels": "parity"})
    assert forced.status_code == 400
    assert forced.json()["detail"] == "Champs invalides."
    assert client.get("/v1/context", headers=headers).json()["week_labels"] == "ab"

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    stats = example.json()["planning"]["stats"]
    assert stats["assignments"] == 92
    assert len(example.json()["planning"]["warnings"]) == 17
    assert stats["wellbeing"] == {"held": 10, "total": 12}
    assert stats["below_role"] == 47


def test_seed_example_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    response = client.post("/v1/context/seed-example", headers=_bearer("x"))
    assert response.status_code == 503
    assert response.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


def _assert_seeded_context(body: dict) -> dict[str, str]:
    assert body["ready"]["salle"] is True
    assert body["ready"]["cuisine"] is False
    assert body["services"] == ["midday", "evening"]
    assert body["week_labels"] == "ab"
    ids = {person["id"] for person in body["employees"]}
    assert {"diane", "theo"} <= ids
    tokens = {person["id"]: person["invite_token"] for person in body["employees"]}
    assert all(token and token != person_id for person_id, token in tokens.items())
    return tokens


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_seed_example_smashes_context_clears_cycles_and_unlinks():
    client = _client()
    email = f"seed-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    restaurant_id = registered.json()["me"]["restaurant_id"]
    assert restaurant_id != "saint-cloud"

    empty = client.get("/v1/context", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["name"] == ""

    seeded = client.post("/v1/context/seed-example", headers=headers)
    assert seeded.status_code == 200
    first = seeded.json()
    assert first["name"] == ""
    first_tokens = _assert_seeded_context(first)
    again = client.get("/v1/context", headers=headers)
    assert again.status_code == 200
    assert again.json() == first
    cycles = client.get("/v1/cycles", headers=headers)
    assert cycles.status_code == 200
    assert cycles.json() == {"published": {"salle": None, "cuisine": None}}

    named = client.patch("/v1/context", headers=headers, json={"name": "Chez Seed"})
    assert named.status_code == 200
    assert named.json()["name"] == "Chez Seed"

    second = client.post("/v1/context/seed-example", headers=headers)
    assert second.status_code == 200
    assert second.json()["name"] == "Chez Seed"
    second_tokens = _assert_seeded_context(second.json())
    assert second_tokens != first_tokens
    assert client.get("/v1/cycles", headers=headers).json() == {"published": {"salle": None, "cuisine": None}}

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id, "Chez Seed"))
    assert patched.status_code == 200
    generated = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    assert generated.json()["published"]["salle"]["assignments"]
    company_code = patched.json()["company_code"]
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
    emp_token = employee.json()["token"]
    assert client.get("/v1/me", headers=_bearer(emp_token)).status_code == 200

    smash = client.post("/v1/context/seed-example", headers=headers)
    assert smash.status_code == 200
    assert smash.json()["name"] == "Chez Seed"
    _assert_seeded_context(smash.json())
    assert client.get("/v1/cycles", headers=headers).json() == {"published": {"salle": None, "cuisine": None}}
    invites = client.get(f"/v1/invites/{company_code}")
    assert invites.status_code == 200
    invite_ids = {person["id"] for person in invites.json()["employees"]}
    assert {"diane", "theo"} <= invite_ids
    assert fiche_id not in invite_ids
    assert client.get("/v1/me", headers=_bearer(emp_token)).status_code == 401

    assert client.post("/v1/context/seed-example", headers=_bearer(emp_token)).status_code == 401
    assert client.post("/v1/context/seed-example").status_code == 401

    linked = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"diane-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": company_code,
            "employee_id": "diane",
        },
    )
    assert linked.status_code == 201
    employee_seed = client.post("/v1/context/seed-example", headers=_bearer(linked.json()["token"]))
    assert employee_seed.status_code == 403
    assert employee_seed.json()["detail"] == "Action réservée au restaurateur."

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    assert client.get("/v1/me", headers=_bearer(logged.json()["token"])).status_code == 200
