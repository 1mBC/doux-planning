from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.app import app
from doux_planning.api.db import (
    AccountEmail,
    AuthSession,
    Company,
    EmployeeAccountRow,
    reset_engine,
    session_scope,
)
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_delete_staff_schema():
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


def _two_fiches_patch(salle_id: str, cuisine_id: str) -> dict:
    return {
        "name": "Chez Delete",
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


def _register_company(client: TestClient) -> tuple[str, str]:
    registered = client.post(
        "/v1/auth/register",
        json={
            "kind": "company",
            "email": f"del-{secrets.token_hex(4)}@example.com",
            "password": "password1",
        },
    )
    assert registered.status_code == 201
    return registered.json()["token"], registered.json()["me"]["restaurant_id"]


def _register_employee(client: TestClient, company_code: str, fiche_id: str) -> tuple[str, str]:
    email = f"emp-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": email,
            "password": "password1",
            "company_code": company_code,
            "employee_id": fiche_id,
        },
    )
    assert registered.status_code == 201, registered.text
    return registered.json()["token"], email


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_delete_linked_staff_keeps_account_login_planning_and_link():
    client = _client()
    company_token, restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]
    emp_token, email = _register_employee(client, company_code, salle_id)

    deleted = client.delete(f"/v1/staff/{salle_id}", headers=headers)
    assert deleted.status_code == 200
    ids = {person["id"] for person in deleted.json()["employees"]}
    assert salle_id not in ids
    assert cuisine_id in ids
    again = client.get("/v1/context", headers=headers)
    assert again.status_code == 200
    assert again.json() == deleted.json()
    assert salle_id not in {person["id"] for person in again.json()["employees"]}

    with session_scope() as session:
        account = session.scalars(select(EmployeeAccountRow).where(EmployeeAccountRow.email == email)).one()
        assert account.restaurant_id is None
        assert account.employee_id is None
        assert session.get(AccountEmail, email) is not None
        stored = session.get(AuthSession, hashlib.sha256(emp_token.encode()).hexdigest())
        assert stored is None

    assert client.get("/v1/me", headers=_bearer(emp_token)).status_code == 401

    logged = client.post("/v1/auth/login", json={"email": email, "password": "password1"})
    assert logged.status_code == 200
    me = logged.json()["me"]
    assert me["kind"] == "employee"
    assert me["email"] == email
    assert me["employee_id"] is None
    assert me["restaurant_id"] is None
    fresh = logged.json()["token"]
    mine = client.get("/v1/me", headers=_bearer(fresh))
    assert mine.status_code == 200
    assert mine.json()["employee_id"] is None
    assert mine.json()["restaurant_id"] is None

    planning = client.get("/v1/me/planning", headers=_bearer(fresh))
    assert planning.status_code == 409
    assert planning.json()["detail"] == "Vous n'êtes rattaché à aucun restaurant."

    linked = client.post(
        "/v1/auth/link",
        headers=_bearer(fresh),
        json={"company_code": company_code, "employee_id": cuisine_id},
    )
    assert linked.status_code == 200
    assert linked.json()["kind"] == "employee"
    assert linked.json()["employee_id"] == cuisine_id
    assert linked.json()["restaurant_id"] == restaurant_id
    assert linked.json()["email"] == email


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_patch_omit_linked_fiche_stays_409():
    client = _client()
    company_token, _restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    _register_employee(client, patched.json()["company_code"], salle_id)
    omitted = client.patch("/v1/context", headers=headers, json={"employees": []})
    assert omitted.status_code == 409
    assert omitted.json()["detail"] == "Cette fiche a déjà un compte."
    still = client.get("/v1/context", headers=headers)
    assert salle_id in {person["id"] for person in still.json()["employees"]}


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_delete_salle_keeps_cuisine_published_and_live():
    client = _client()
    company_token, restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    cuisine_published = {"marker": "cuisine-published", "fiche": cuisine_id}
    cuisine_live = {"marker": "cuisine-live"}
    salle_published = {"marker": "salle-published", "fiche": salle_id}
    salle_live = {"marker": "salle-live"}
    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        company.published_cycles = {"salle": salle_published, "cuisine": cuisine_published}
        company.live_sandboxes = {"salle": salle_live, "cuisine": cuisine_live}
        flag_modified(company, "published_cycles")
        flag_modified(company, "live_sandboxes")
    _register_employee(client, patched.json()["company_code"], salle_id)
    deleted = client.delete(f"/v1/staff/{salle_id}", headers=headers)
    assert deleted.status_code == 200
    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        assert company.published_cycles["salle"] is None
        assert company.published_cycles["cuisine"] == cuisine_published
        assert company.live_sandboxes["salle"] is None
        assert company.live_sandboxes["cuisine"] == cuisine_live


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_delete_staff_employee_forbidden_and_unknown_404():
    client = _client()
    company_token, _restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    emp_token, _email = _register_employee(client, patched.json()["company_code"], salle_id)
    forbidden = client.delete(f"/v1/staff/{salle_id}", headers=_bearer(emp_token))
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Action réservée au restaurateur."
    missing = client.delete(f"/v1/staff/ghost-{secrets.token_hex(4)}", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Fiche introuvable."
    other_token, _other_id = _register_company(client)
    other = client.delete(f"/v1/staff/{salle_id}", headers=_bearer(other_token))
    assert other.status_code == 404
    assert other.json()["detail"] == "Fiche introuvable."
    still = client.get("/v1/context", headers=headers)
    assert salle_id in {person["id"] for person in still.json()["employees"]}


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_auth_link_error_table():
    client = _client()
    company_token, _restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]
    emp_a_token, email_a = _register_employee(client, company_code, salle_id)
    emp_b_token, _email_b = _register_employee(client, company_code, cuisine_id)

    company_link = client.post(
        "/v1/auth/link",
        headers=headers,
        json={"company_code": company_code, "employee_id": salle_id},
    )
    assert company_link.status_code == 403
    assert company_link.json()["detail"] == "Action réservée au salarié."

    already = client.post(
        "/v1/auth/link",
        headers=_bearer(emp_b_token),
        json={"company_code": company_code, "employee_id": salle_id},
    )
    assert already.status_code == 409
    assert already.json()["detail"] == "Vous êtes déjà rattaché à un restaurant."

    deleted = client.delete(f"/v1/staff/{salle_id}", headers=headers)
    assert deleted.status_code == 200
    logged = client.post("/v1/auth/login", json={"email": email_a, "password": "password1"})
    assert logged.status_code == 200
    unaffiliated = logged.json()["token"]
    assert client.get("/v1/me", headers=_bearer(emp_a_token)).status_code == 401

    missing_fields = client.post("/v1/auth/link", headers=_bearer(unaffiliated), json={})
    assert missing_fields.status_code == 400
    assert missing_fields.json()["detail"] == "Champs invalides."

    bad_code = client.post(
        "/v1/auth/link",
        headers=_bearer(unaffiliated),
        json={"company_code": "not-a-code", "employee_id": cuisine_id},
    )
    assert bad_code.status_code == 400
    assert bad_code.json()["detail"] == "Code entreprise ou jeton invalide."

    unknown = client.post(
        "/v1/auth/link",
        headers=_bearer(unaffiliated),
        json={"company_code": company_code, "employee_id": f"ghost-{secrets.token_hex(4)}"},
    )
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Fiche introuvable."

    taken = client.post(
        "/v1/auth/link",
        headers=_bearer(unaffiliated),
        json={"company_code": company_code, "employee_id": cuisine_id},
    )
    assert taken.status_code == 409
    assert taken.json()["detail"] == "Cette fiche a déjà un compte."


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_persist_maximal_fails_when_assignment_fiche_gone():
    from doux_planning.api.generate import StaleGenerateStaff, persist_maximal_result
    from doux_planning.types import Team

    client = _client()
    company_token, restaurant_id = _register_company(client)
    headers = _bearer(company_token)
    salle_id = f"emma-{secrets.token_hex(4)}"
    cuisine_id = f"karim-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_two_fiches_patch(salle_id, cuisine_id))
    assert patched.status_code == 200
    cuisine_blob = {"marker": "cuisine-keep"}
    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        company.published_cycles = {"salle": {"marker": "salle-old"}, "cuisine": cuisine_blob}
        flag_modified(company, "published_cycles")

    def _stale_generate(state, team, search, engine_ref=None):
        class _Result:
            assignments = (type("Shift", (), {"employee_id": "ghost-gone"})(),)

        class _Cycle:
            result = _Result()

        state.published_cycles[team] = _Cycle()
        return state

    with pytest.raises(StaleGenerateStaff) as raised:
        persist_maximal_result(restaurant_id, Team.SALLE, generate_fn=_stale_generate)
    assert str(raised.value) == "Un salarié du cycle n'est plus dans l'équipe."
    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        assert company.published_cycles["cuisine"] == cuisine_blob
        assert company.published_cycles["salle"] == {"marker": "salle-old"}
