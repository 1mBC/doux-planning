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
    export = client.get("/v1/context/export", headers=_bearer("x"))
    assert export.status_code == 503
    assert export.json()["detail"] == "Base indisponible."
    imported = client.post("/v1/context/import", headers=_bearer("x"), json={"export_version": 1})
    assert imported.status_code == 503
    assert imported.json()["detail"] == "Base indisponible."


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
        "weekend_rest_day": False,
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
            "weekend_rest_day": False,
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
        "weekend_rest_day": False,
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


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_context_weekend_rest_day_persist_and_legacy_key():
    client = _client()
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"wrd-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert registered.status_code == 201
    headers = _bearer(registered.json()["token"])
    fiche_id = f"emma-{secrets.token_hex(4)}"
    posed = _fiche_payload(fiche_id, weekend=None)
    posed["wellbeing"] = {
        "consecutive_rest": False,
        "weekend_rest_day": True,
        "weekend": None,
        "max_services": {},
        "max_coupures_per_week": None,
    }
    patched = client.patch("/v1/context", headers=headers, json={"employees": [posed]})
    assert patched.status_code == 200
    assert patched.json()["employees"][0]["wellbeing"]["weekend_rest_day"] is True
    reset_engine()
    again = client.get("/v1/context", headers=headers)
    assert again.status_code == 200
    assert again.json()["employees"][0]["wellbeing"]["weekend_rest_day"] is True

    omitted = _fiche_payload(fiche_id, weekend=None)
    omitted["wellbeing"] = {
        "consecutive_rest": False,
        "weekend": None,
        "max_services": {},
        "max_coupures_per_week": None,
    }
    without = client.patch("/v1/context", headers=headers, json={"employees": [omitted]})
    assert without.status_code == 200
    assert without.json()["employees"][0]["wellbeing"]["weekend_rest_day"] is False

    legacy_list = client.patch(
        "/v1/context",
        headers=headers,
        json={"employees": [{**_fiche_payload(fiche_id, weekend=None), "wellbeing": ["at_least_one_weekend_rest_day"]}]},
    )
    assert legacy_list.status_code == 400
    assert legacy_list.json()["detail"] == "Champs invalides."
    legacy_key = client.patch(
        "/v1/context",
        headers=headers,
        json={
            "employees": [
                {
                    **_fiche_payload(fiche_id, weekend=None),
                    "wellbeing": {"at_least_one_weekend_rest_day": True},
                }
            ]
        },
    )
    assert legacy_key.status_code == 400
    assert legacy_key.json()["detail"] == "Champs invalides."
    assert client.get("/v1/context", headers=headers).json()["employees"][0]["wellbeing"]["weekend_rest_day"] is False
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert example.json()["planning"]["stats"]["wellbeing"] == {"held": 10, "total": 12}


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


def _collect_keys(value) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(_collect_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_collect_keys(item))
    return keys


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_context_export_import_strips_and_smashes():
    client = _client()
    password = "password1"
    source = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"exp-{secrets.token_hex(4)}@example.com", "password": password},
    )
    assert source.status_code == 201
    source_headers = _bearer(source.json()["token"])
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=source_headers, json=_salle_patch(fiche_id, "Chez Export"))
    assert patched.status_code == 200
    assert patched.json()["ready"]["salle"] is True
    source_code = patched.json()["company_code"]
    source_tokens = {person["id"]: person["invite_token"] for person in patched.json()["employees"]}

    exported = client.get("/v1/context/export", headers=source_headers)
    assert exported.status_code == 200
    payload = exported.json()
    assert payload["export_version"] == 1
    assert payload["name"] == "Chez Export"
    assert payload["services"] == ["midday"]
    assert set(payload) == {
        "export_version",
        "name",
        "services",
        "ladders",
        "employees",
        "types",
        "typical_week",
    }
    assert _collect_keys(payload).isdisjoint({"company_code", "invite_token"})
    assert all("invite_token" not in person for person in payload["employees"])

    empty = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"imp-{secrets.token_hex(4)}@example.com", "password": password},
    )
    assert empty.status_code == 201
    empty_headers = _bearer(empty.json()["token"])
    target_before = client.get("/v1/context", headers=empty_headers)
    assert target_before.status_code == 200
    assert target_before.json()["ready"]["salle"] is False
    kept_code = target_before.json()["company_code"]

    tainted = dict(payload)
    tainted["company_code"] = source_code
    tainted["legal_context_id"] = "elsewhere"
    tainted["ready"] = {"salle": False, "cuisine": True}
    tainted["week_labels"] = "parity"
    tainted["invite_token"] = "stolen"
    tainted["employees"] = [{**person, "invite_token": "stolen-fiche"} for person in payload["employees"]]

    imported = client.post("/v1/context/import", headers=empty_headers, json=tainted)
    assert imported.status_code == 200
    body = imported.json()
    assert body == client.get("/v1/context", headers=empty_headers).json()
    assert body["name"] == "Chez Export"
    assert body["ready"]["salle"] is True
    assert body["ready"]["cuisine"] is False
    assert body["company_code"] == kept_code
    assert body["company_code"] != source_code
    assert body["legal_context_id"] == "france"
    imported_tokens = {person["id"]: person["invite_token"] for person in body["employees"]}
    assert fiche_id in imported_tokens
    assert all(token and token != person_id for person_id, token in imported_tokens.items())
    assert imported_tokens != source_tokens
    assert "stolen-fiche" not in imported_tokens.values()

    generated = client.post(
        "/v1/generate",
        headers=empty_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    assert generated.json()["published"]["salle"]["assignments"]
    employee = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"emma-{secrets.token_hex(4)}@example.com",
            "password": password,
            "company_code": kept_code,
            "employee_id": fiche_id,
        },
    )
    assert employee.status_code == 201
    emp_token = employee.json()["token"]
    assert client.get("/v1/me", headers=_bearer(emp_token)).status_code == 200

    smash = client.post("/v1/context/import", headers=empty_headers, json=payload)
    assert smash.status_code == 200
    assert smash.json()["name"] == "Chez Export"
    assert smash.json()["ready"]["salle"] is True
    assert smash.json()["company_code"] == kept_code
    smash_tokens = {person["id"]: person["invite_token"] for person in smash.json()["employees"]}
    assert smash_tokens != imported_tokens
    assert client.get("/v1/cycles", headers=empty_headers).json() == {
        "published": {"salle": None, "cuisine": None}
    }
    assert client.get("/v1/me", headers=_bearer(emp_token)).status_code == 401

    bad_version = dict(payload)
    bad_version["export_version"] = 2
    rejected = client.post("/v1/context/import", headers=empty_headers, json=bad_version)
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "Champs invalides."

    forbidden = client.post("/v1/context/import", headers=_bearer(employee.json()["token"]), json=payload)
    assert forbidden.status_code == 401
    still_linked = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"emma2-{secrets.token_hex(4)}@example.com",
            "password": password,
            "company_code": kept_code,
            "employee_id": fiche_id,
        },
    )
    assert still_linked.status_code == 201
    employee_import = client.post(
        "/v1/context/import",
        headers=_bearer(still_linked.json()["token"]),
        json=payload,
    )
    assert employee_import.status_code == 403
    assert employee_import.json()["detail"] == "Action réservée au restaurateur."
    assert client.get("/v1/context/export", headers=_bearer(still_linked.json()["token"])).status_code == 403
    assert client.get("/v1/context/export").status_code == 401
    assert client.post("/v1/context/import", json=payload).status_code == 401

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    logged = client.post("/v1/auth/login", json={"email": empty.json()["me"]["email"], "password": password})
    assert logged.status_code == 200
    assert client.get("/v1/me", headers=_bearer(logged.json()["token"])).status_code == 200


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_context_coerce_legacy_wellbeing_on_read():
    from sqlalchemy.orm.attributes import flag_modified

    from doux_planning.api.db import StaffFiche, session_scope

    client = _client()
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"coerce-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    restaurant_id = registered.json()["me"]["restaurant_id"]
    fiche_id = f"emma-{secrets.token_hex(4)}"
    seeded = _salle_patch(fiche_id)
    seeded["services"] = ["morning", "midday", "evening"]
    patched = client.patch("/v1/context", headers=headers, json=seeded)
    assert patched.status_code == 200

    legacy_list = [
        "two_consecutive_rest_days",
        "weekend_off_every_two_weeks",
        "at_least_one_weekend_rest_day",
        "max_two_coupures_per_week",
    ]
    legacy_indispos = [
        {"weekday": "monday", "every_morning": True},
        {"weekday": "tuesday", "service_id": None},
    ]
    with session_scope() as session:
        fiche = session.get(StaffFiche, (restaurant_id, fiche_id))
        assert fiche is not None
        fiche.wellbeing = legacy_list
        fiche.unavailabilities = legacy_indispos
        flag_modified(fiche, "wellbeing")
        flag_modified(fiche, "unavailabilities")

    first = client.get("/v1/context", headers=headers)
    assert first.status_code == 200
    wellbeing = first.json()["employees"][0]["wellbeing"]
    assert wellbeing == {
        "consecutive_rest": True,
        "weekend_rest_day": True,
        "weekend": "every_two",
        "max_services": {},
        "max_coupures_per_week": 2,
    }
    unavails = first.json()["employees"][0]["unavailabilities"]
    assert {"weekday": "monday", "service_id": "morning"} in unavails
    assert {"weekday": "tuesday", "service_id": "midday"} in unavails
    assert {"weekday": "tuesday", "service_id": "evening"} in unavails
    assert all("every_morning" not in row and row.get("service_id") for row in unavails)
    exported = client.get("/v1/context/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["employees"][0]["wellbeing"] == wellbeing
    assert isinstance(exported.json()["employees"][0]["wellbeing"], dict)

    second = client.get("/v1/context", headers=headers)
    assert second.status_code == 200
    assert second.json()["employees"][0]["wellbeing"] == wellbeing
    assert second.json()["employees"][0]["unavailabilities"] == unavails

    with session_scope() as session:
        healed = session.get(StaffFiche, (restaurant_id, fiche_id))
        assert isinstance(healed.wellbeing, dict)
        assert healed.wellbeing == wellbeing
        assert not any("every_morning" in row for row in healed.unavailabilities)

    with session_scope() as session:
        fiche = session.get(StaffFiche, (restaurant_id, fiche_id))
        fiche.wellbeing = ["no_evening_service"]
        flag_modified(fiche, "wellbeing")

    evening = client.get("/v1/context", headers=headers)
    assert evening.status_code == 200
    assert evening.json()["employees"][0]["wellbeing"]["max_services"] == {"evening": 0}

    list_patch = client.patch(
        "/v1/context",
        headers=headers,
        json={"employees": [{**_fiche_payload(fiche_id, weekend=None), "wellbeing": legacy_list}]},
    )
    assert list_patch.status_code == 400
    assert list_patch.json()["detail"] == "Champs invalides."
    removed_patch = client.patch(
        "/v1/context",
        headers=headers,
        json={
            "employees": [
                {
                    **_fiche_payload(fiche_id, weekend=None),
                    "wellbeing": {"at_least_one_weekend_rest_day": True},
                }
            ]
        },
    )
    assert removed_patch.status_code == 400
    assert removed_patch.json()["detail"] == "Champs invalides."
    every_patch = client.patch(
        "/v1/context",
        headers=headers,
        json={
            "employees": [
                _fiche_payload(
                    fiche_id,
                    weekend=None,
                    unavailabilities=[{"weekday": "monday", "every_morning": True}],
                )
            ]
        },
    )
    assert every_patch.status_code == 400
    assert every_patch.json()["detail"] == "Champs invalides."

    core = {
        "consecutive_rest": True,
        "weekend_rest_day": False,
        "weekend": "even",
        "max_services": {"evening": 1},
        "max_coupures_per_week": 2,
    }
    core_fiche = _fiche_payload(fiche_id, weekend="even")
    core_fiche["wellbeing"] = core
    core_patch = client.patch("/v1/context", headers=headers, json={"employees": [core_fiche]})
    assert core_patch.status_code == 200
    assert core_patch.json()["employees"][0]["wellbeing"] == core
    core_get = client.get("/v1/context", headers=headers)
    assert core_get.status_code == 200
    assert core_get.json()["employees"][0]["wellbeing"] == core

    portable = client.get("/v1/context/export", headers=headers).json()
    portable["employees"][0]["wellbeing"] = legacy_list
    imported = client.post("/v1/context/import", headers=headers, json=portable)
    assert imported.status_code == 400
    assert imported.json()["detail"] == "Champs invalides."
    assert client.get("/v1/context", headers=headers).json()["employees"][0]["wellbeing"] == core

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert example.json()["planning"]["stats"]["wellbeing"] == {"held": 10, "total": 12}
