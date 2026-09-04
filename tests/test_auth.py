from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from doux_planning.api.app import app
from doux_planning.api.db import (
    AuthSession,
    Company,
    RestaurateurAccount,
    StaffFiche,
    reset_engine,
    session_scope,
)


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_auth_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def test_auth_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    response = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": "nodb@example.com", "password": "password1"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    sandbox = client.post("/v1/sandbox/enter")
    assert sandbox.status_code == 200


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_company_register_login_me_logout_and_errors():
    client = _client()
    email = f"resto-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    body = registered.json()
    token = body["token"]
    me = body["me"]
    assert me["kind"] == "company"
    assert me["email"] == email
    assert me["employee_id"] is None
    assert me["restaurant_id"] != "saint-cloud"
    assert token

    with session_scope() as session:
        account = session.scalars(select(RestaurateurAccount).where(RestaurateurAccount.email == email)).one()
        assert account.password_hash != password
        assert account.password_hash.startswith("$argon2")
        stored = session.get(AuthSession, hashlib.sha256(token.encode()).hexdigest())
        assert stored is not None
        assert stored.token_hash != token
        company = session.get(Company, me["restaurant_id"])
        assert company is not None
        assert company.name == ""
        assert company.invite_code

    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    login_token = logged.json()["token"]
    assert logged.json()["me"]["kind"] == "company"

    mine = client.get("/v1/me", headers=_bearer(login_token))
    assert mine.status_code == 200
    assert mine.json()["kind"] == "company"
    assert mine.json()["employee_id"] is None
    assert "token" not in mine.json()

    duplicate = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Cet email est déjà utilisé."

    wrong = client.post("/v1/auth/login", json={"email": email, "password": "wrongpass"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "Email ou mot de passe incorrect."

    closed = client.post("/v1/auth/logout", headers=_bearer(login_token))
    assert closed.status_code == 204
    after = client.get("/v1/me", headers=_bearer(login_token))
    assert after.status_code == 401
    assert after.json()["detail"] == "Session invalide."

    example = client.get("/v1/examples/saint-cloud", headers=_bearer(token))
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    public = client.get("/v1/examples/saint-cloud")
    assert public.status_code == 200
    assert public.json()["planning"]["stats"]["assignments"] == 92

    assert client.post("/v1/sandbox/enter").status_code == 200
    assert client.get("/v1/sandbox").status_code == 200

    assert client.post("/v1/auth/restaurateur/register", json={"email": email, "password": password}).status_code == 404
    assert client.post("/v1/auth/employee/register", json={"email": email, "password": password}).status_code == 404


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_employee_invites_register_qr_and_rotate():
    client = _client()
    email = f"boss-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": "password1"},
    )
    assert registered.status_code == 201
    company_token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        invite_code = company.invite_code
        token_a = secrets.token_urlsafe(16)
        token_b = secrets.token_urlsafe(16)
        fiche_a = f"ada-{secrets.token_hex(4)}"
        fiche_b = f"bea-{secrets.token_hex(4)}"
        session.add(
            StaffFiche(
                id=fiche_a,
                company_id=restaurant_id,
                name="Ada",
                role="commis",
                team="cuisine",
                invite_token=token_a,
            )
        )
        session.add(
            StaffFiche(
                id=fiche_b,
                company_id=restaurant_id,
                name="Bea",
                role="commis",
                team="cuisine",
                invite_token=token_b,
            )
        )

    preview = client.get(f"/v1/invites/{invite_code}")
    assert preview.status_code == 200
    body = preview.json()
    assert body["restaurant_name"] == ""
    ids = {person["id"] for person in body["employees"]}
    assert ids == {fiche_a, fiche_b}
    for person in body["employees"]:
        assert set(person) == {"id", "name", "role", "team"}
        assert "invite_token" not in person
        assert "token" not in person

    employee_a = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"ada-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": invite_code,
            "employee_id": fiche_a,
        },
    )
    assert employee_a.status_code == 201
    assert employee_a.json()["me"]["kind"] == "employee"
    assert employee_a.json()["me"]["employee_id"] == fiche_a
    after_a = client.get(f"/v1/invites/{invite_code}").json()
    assert {person["id"] for person in after_a["employees"]} == {fiche_b}

    again = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"ada2-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": invite_code,
            "employee_id": fiche_a,
        },
    )
    assert again.status_code == 409
    assert again.json()["detail"] == "Cette fiche a déjà un compte."

    employee_b = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"bea-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": invite_code,
            "employee_token": token_b,
        },
    )
    assert employee_b.status_code == 201
    assert employee_b.json()["me"]["employee_id"] == fiche_b
    after_b = client.get(f"/v1/invites/{invite_code}").json()
    assert after_b["employees"] == []

    bad_code = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"bad-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": "not-a-code",
            "employee_id": fiche_a,
        },
    )
    assert bad_code.status_code == 400
    assert bad_code.json()["detail"] == "Code entreprise ou jeton invalide."

    rotated = client.post(
        f"/v1/staff/{fiche_a}/invite-token",
        headers=_bearer(company_token),
    )
    assert rotated.status_code == 200
    new_token = rotated.json()["employee_token"]
    assert new_token
    assert new_token != token_a
    assert rotated.json()["employee_id"] == fiche_a

    old = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"old-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": invite_code,
            "employee_token": token_a,
        },
    )
    assert old.status_code == 400
    assert old.json()["detail"] == "Code entreprise ou jeton invalide."

    fresh = client.post(
        "/v1/auth/register",
        json={
            "kind": "employee",
            "email": f"ada-new-{secrets.token_hex(4)}@example.com",
            "password": "password1",
            "company_code": invite_code,
            "employee_token": new_token,
        },
    )
    assert fresh.status_code == 409
    assert fresh.json()["detail"] == "Cette fiche a déjà un compte."

    employee_forbidden = client.post(
        f"/v1/staff/{fiche_a}/invite-token",
        headers=_bearer(employee_b.json()["token"]),
    )
    assert employee_forbidden.status_code == 403
    assert employee_forbidden.json()["detail"] == "Action réservée au restaurateur."
