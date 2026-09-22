from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from doux_planning.api.app import app, web_dist
from doux_planning.api.auth import (
    DETAIL_ADMIN,
    DETAIL_IMPERSONATE,
    DETAIL_INVALID_FIELDS,
    DETAIL_RESTAURANT_MISSING,
    _hash_token,
    promote_admin_email,
)
from doux_planning.api.db import GenerateLog, ImpersonateToken, reset_engine, session_scope
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_admin_historique_schema():
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


def test_admin_historique_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    headers = _bearer("x")
    cycles = client.get("/v1/admin/restaurants/unknown/cycles", headers=headers)
    assert cycles.status_code == 503
    assert cycles.json()["detail"] == "Base indisponible."
    context = client.get("/v1/admin/restaurants/unknown/context", headers=headers)
    assert context.status_code == 503
    mint = client.post("/v1/admin/impersonate", headers=headers, json={"restaurant_id": "x"})
    assert mint.status_code == 503
    consume = client.post("/v1/auth/impersonate", json={"token": "x"})
    assert consume.status_code == 503


def test_spa_impersonate_and_admin_planning_serve_index():
    dist = web_dist()
    if dist is None:
        pytest.skip("web/dist absent")
    index = (dist / "index.html").read_text(encoding="utf-8")
    client = _client()
    for path in ("/impersonate/example-token", "/admin/planning/example-id"):
        page = client.get(path)
        assert page.status_code == 200
        assert page.text == index


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_historique_note_view_impersonate(monkeypatch):
    client = _client()
    password = "password1"
    admin_email = f"hist-admin-{secrets.token_hex(4)}@example.com"
    other_email = f"hist-resto-{secrets.token_hex(4)}@example.com"

    admin_token, admin_restaurant_id = _register_company(client, admin_email, password)
    monkeypatch.setenv("ADMIN_EMAIL", admin_email)
    promote_admin_email()
    admin_headers = _bearer(admin_token)
    assert client.get("/v1/me", headers=admin_headers).json()["admin"] is True

    other_token, other_restaurant_id = _register_company(client, other_email, password)
    other_headers = _bearer(other_token)
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=other_headers, json=_salle_patch(fiche_id, "Chez Historique"))
    assert patched.status_code == 200

    generated = client.post(
        "/v1/generate",
        headers=other_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    slot = generated.json()["published"]["salle"]["versions"]["minimal"]
    expected_score = slot["score"]["global"]
    assert isinstance(expected_score, (int, float))

    with session_scope() as db:
        row = db.scalars(select(GenerateLog).where(GenerateLog.email == other_email)).one()
        assert row.restaurant_id == other_restaurant_id
        assert row.score_global == expected_score

    listed = client.get("/v1/admin/generates", headers=admin_headers)
    assert listed.status_code == 200
    entry = next(item for item in listed.json()["entries"] if item["email"] == other_email)
    assert "restaurant_id" in entry
    assert "score_global" in entry
    assert entry["restaurant_id"] == other_restaurant_id
    assert entry["score_global"] == expected_score

    old_id = f"legacy-hist-{secrets.token_hex(4)}"
    with session_scope() as db:
        db.add(
            GenerateLog(
                id=old_id,
                created_at=datetime.now(timezone.utc) - timedelta(days=1),
                email="legacy-hist@example.com",
                restaurant_name="Legacy",
                team="salle",
                search_effort=None,
                duration_seconds=None,
                warnings=[],
            )
        )
    with_legacy = client.get("/v1/admin/generates", headers=admin_headers)
    legacy = next(item for item in with_legacy.json()["entries"] if item["id"] == old_id)
    assert "restaurant_id" in legacy
    assert "score_global" in legacy
    assert legacy["restaurant_id"] is None
    assert legacy["score_global"] is None

    company_cycles = client.get("/v1/cycles", headers=other_headers)
    assert company_cycles.status_code == 200
    admin_cycles = client.get(
        f"/v1/admin/restaurants/{other_restaurant_id}/cycles",
        headers=admin_headers,
    )
    assert admin_cycles.status_code == 200
    assert admin_cycles.json() == company_cycles.json()
    assert admin_cycles.json()["published"]["salle"]["versions"]["minimal"]["assignments"]

    company_ctx = client.get("/v1/context", headers=other_headers)
    assert company_ctx.status_code == 200
    admin_ctx = client.get(
        f"/v1/admin/restaurants/{other_restaurant_id}/context",
        headers=admin_headers,
    )
    assert admin_ctx.status_code == 200
    assert admin_ctx.json() == company_ctx.json()
    assert admin_ctx.json()["name"] == "Chez Historique"
    assert any(emp.get("invite_token") for emp in admin_ctx.json()["employees"])

    missing_cycles = client.get("/v1/admin/restaurants/does-not-exist/cycles", headers=admin_headers)
    assert missing_cycles.status_code == 404
    assert missing_cycles.json()["detail"] == DETAIL_RESTAURANT_MISSING
    missing_ctx = client.get("/v1/admin/restaurants/does-not-exist/context", headers=admin_headers)
    assert missing_ctx.status_code == 404
    assert missing_ctx.json()["detail"] == DETAIL_RESTAURANT_MISSING

    forbidden_cycles = client.get(
        f"/v1/admin/restaurants/{other_restaurant_id}/cycles",
        headers=other_headers,
    )
    assert forbidden_cycles.status_code == 403
    assert forbidden_cycles.json()["detail"] == DETAIL_ADMIN
    forbidden_ctx = client.get(
        f"/v1/admin/restaurants/{other_restaurant_id}/context",
        headers=other_headers,
    )
    assert forbidden_ctx.status_code == 403
    assert forbidden_ctx.json()["detail"] == DETAIL_ADMIN
    forbidden_mint = client.post(
        "/v1/admin/impersonate",
        headers=other_headers,
        json={"restaurant_id": other_restaurant_id},
    )
    assert forbidden_mint.status_code == 403
    assert forbidden_mint.json()["detail"] == DETAIL_ADMIN

    assert client.get(f"/v1/admin/restaurants/{other_restaurant_id}/cycles").status_code == 401
    assert client.post("/v1/admin/impersonate", json={"restaurant_id": other_restaurant_id}).status_code == 401

    bad_fields = client.post("/v1/admin/impersonate", headers=admin_headers, json={"restaurant_id": 12})
    assert bad_fields.status_code == 400
    assert bad_fields.json()["detail"] == DETAIL_INVALID_FIELDS
    missing_field = client.post("/v1/admin/impersonate", headers=admin_headers, json={})
    assert missing_field.status_code == 400
    assert missing_field.json()["detail"] == DETAIL_INVALID_FIELDS
    mint_404 = client.post(
        "/v1/admin/impersonate",
        headers=admin_headers,
        json={"restaurant_id": "does-not-exist"},
    )
    assert mint_404.status_code == 404
    assert mint_404.json()["detail"] == DETAIL_RESTAURANT_MISSING

    minted = client.post(
        "/v1/admin/impersonate",
        headers={
            **admin_headers,
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "doux.example",
        },
        json={"restaurant_id": other_restaurant_id},
    )
    assert minted.status_code == 200
    url = minted.json()["url"]
    expires_at = minted.json()["expires_at"]
    assert url.startswith("https://doux.example/impersonate/")
    assert "/impersonate/" in url
    assert "T" in expires_at
    opaque = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    assert opaque

    consumed = client.post("/v1/auth/impersonate", json={"token": opaque})
    assert consumed.status_code == 200
    body = consumed.json()
    assert isinstance(body["token"], str)
    assert body["me"]["kind"] == "company"
    assert body["me"]["email"] == other_email
    assert body["me"]["restaurant_id"] == other_restaurant_id
    assert body["me"]["employee_id"] is None
    assert body["me"]["admin"] is False

    impersonated_me = client.get("/v1/me", headers=_bearer(body["token"]))
    assert impersonated_me.status_code == 200
    assert impersonated_me.json()["kind"] == "company"
    assert impersonated_me.json()["restaurant_id"] == other_restaurant_id
    assert impersonated_me.json()["admin"] is False

    second = client.post("/v1/auth/impersonate", json={"token": opaque})
    assert second.status_code == 401
    assert second.json()["detail"] == DETAIL_IMPERSONATE

    still_admin = client.get("/v1/me", headers=admin_headers)
    assert still_admin.status_code == 200
    assert still_admin.json()["admin"] is True
    assert still_admin.json()["restaurant_id"] == admin_restaurant_id

    still_other = client.get("/v1/me", headers=other_headers)
    assert still_other.status_code == 200
    assert still_other.json()["email"] == other_email
    assert still_other.json()["admin"] is False

    expired_opaque = secrets.token_urlsafe(32)
    with session_scope() as db:
        db.add(
            ImpersonateToken(
                token_hash=_hash_token(expired_opaque),
                account_id="unused",
                restaurant_id=other_restaurant_id,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                consumed_at=None,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
            )
        )
    expired = client.post("/v1/auth/impersonate", json={"token": expired_opaque})
    assert expired.status_code == 401
    assert expired.json()["detail"] == DETAIL_IMPERSONATE

    unknown = client.post("/v1/auth/impersonate", json={"token": "not-a-real-token"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == DETAIL_IMPERSONATE

    invalid_consume = client.post("/v1/auth/impersonate", json={"token": 1})
    assert invalid_consume.status_code == 400
    assert invalid_consume.json()["detail"] == DETAIL_INVALID_FIELDS
