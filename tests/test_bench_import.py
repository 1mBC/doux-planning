from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, DETAIL_INVALID_FIELDS, DETAIL_RESTAURANT_MISSING, promote_admin_email
from doux_planning.api.bench_import import DETAIL_NO_SALLE
from doux_planning.api.db import reset_engine
from doux_planning.bench import load_bench_dataset
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_import_schema():
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


def _cuisine_patch(fiche_id: str, name: str) -> dict:
    return {
        "name": name,
        "services": ["midday"],
        "ladders": {
            "salle": None,
            "cuisine": {
                "roles": [{"name": "CHEF", "level": 4}, {"name": "COMMIS", "level": 1}],
                "substitution_explained": True,
            },
        },
        "employees": [
            {
                "id": fiche_id,
                "name": "Karim",
                "team": "cuisine",
                "role": {"name": "CHEF", "level": 4, "team": "cuisine"},
                "contractual_hours_per_week": 39,
            }
        ],
        "types": [
            {
                "id": "cuisine-midi",
                "name": "Cuisine midi",
                "team": "cuisine",
                "service_id": "midday",
                "arrivals": [{"time_minutes": 10 * 60, "post_levels": [4]}],
                "departures": [{"time_minutes": 16 * 60, "remaining_post_levels": []}],
            }
        ],
        "typical_week": {"salle": None, "cuisine": _open_week("cuisine-midi")},
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


def test_bench_import_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    headers = _bearer("x")
    preview = client.get("/v1/admin/restaurants/unknown/import-preview", headers=headers)
    assert preview.status_code == 503
    assert preview.json()["detail"] == "Base indisponible."
    imported = client.post("/v1/admin/bench/import", headers=headers, json={"restaurant_id": "x"})
    assert imported.status_code == 503


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_bench_import_preview_flags_override_runs_cuisine_and_auth(monkeypatch):
    client = _client()
    password = "password1"
    admin_email = f"imp-admin-{secrets.token_hex(4)}@example.com"
    resto_email = f"imp-resto-{secrets.token_hex(4)}@example.com"
    cuisine_email = f"imp-cuisine-{secrets.token_hex(4)}@example.com"

    admin_token, _admin_rid = _register_company(client, admin_email, password)
    admin_headers = _promote(client, admin_email, admin_token, monkeypatch)

    other_token, restaurant_id = _register_company(client, resto_email, password)
    other_headers = _bearer(other_token)
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=other_headers, json=_salle_patch(fiche_id, "Chez Import"))
    assert patched.status_code == 200
    assert patched.json()["ready"]["salle"] is True
    before_context = patched.json()

    preview = client.get(f"/v1/admin/restaurants/{restaurant_id}/import-preview", headers=admin_headers)
    assert preview.status_code == 200
    body = preview.json()
    assert body["restaurant_id"] == restaurant_id
    assert body["restaurant_name"] == "Chez Import"
    assert body["email"] == resto_email
    assert body["salle"]["ready"] is True
    assert body["salle"]["manuel_published"] is False
    assert body["salle"]["computes_published"] == {"minimal": False, "optimized": False, "maximal": False}
    assert body["cuisine"]["ready"] is False
    assert body["generate_count"] == 0

    generated = client.post(
        "/v1/generate",
        headers=other_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    after_generate = client.get(f"/v1/admin/restaurants/{restaurant_id}/import-preview", headers=admin_headers)
    assert after_generate.status_code == 200
    assert after_generate.json()["salle"]["computes_published"]["minimal"] is True
    assert after_generate.json()["generate_count"] == 1

    missing = client.get("/v1/admin/restaurants/does-not-exist/import-preview", headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == DETAIL_RESTAURANT_MISSING
    forbidden = client.get(f"/v1/admin/restaurants/{restaurant_id}/import-preview", headers=other_headers)
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == DETAIL_ADMIN
    unauth = client.get(f"/v1/admin/restaurants/{restaurant_id}/import-preview")
    assert unauth.status_code == 401

    both_false = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": restaurant_id, "include_salle": False, "include_cuisine": False},
    )
    assert both_false.status_code == 400
    assert both_false.json()["detail"] == DETAIL_INVALID_FIELDS
    bad_score = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": restaurant_id, "manual_score": 11},
    )
    assert bad_score.status_code == 400
    assert bad_score.json()["detail"] == DETAIL_INVALID_FIELDS
    missing_import = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": "does-not-exist"},
    )
    assert missing_import.status_code == 404
    assert missing_import.json()["detail"] == DETAIL_RESTAURANT_MISSING
    forbidden_import = client.post(
        "/v1/admin/bench/import",
        headers=other_headers,
        json={"restaurant_id": restaurant_id},
    )
    assert forbidden_import.status_code == 403
    assert forbidden_import.json()["detail"] == DETAIL_ADMIN

    imported = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={
            "restaurant_id": restaurant_id,
            "manual_score": 7.26,
            "comment": "  note banc  ",
            "include_runs": True,
        },
    )
    assert imported.status_code == 200
    payload = imported.json()
    assert payload["category"] == "imported"
    assert payload["origin"] == "imported"
    assert payload["id"].startswith("imp-")
    assert payload["name"] == "Chez Import"
    assert payload["challenge_fr"] == "note banc"
    assert payload["comment"] == "note banc"
    assert payload["manual_score_override"] == 7.3
    assert payload["included"]["salle"] is True
    assert payload["included"]["runs"] is True

    after_import = client.get("/v1/context", headers=other_headers)
    assert after_import.status_code == 200
    assert after_import.json()["name"] == before_context["name"]
    assert after_import.json()["employees"][0]["id"] == fiche_id

    versions = client.get("/v1/admin/bench/versions", headers=admin_headers)
    assert versions.status_code == 200
    datasets = versions.json()["datasets"]
    halles = next(item for item in datasets if item["category"] == "tight" and item["id"] == "halles")
    assert halles["origin"] == "catalogue"
    assert halles["comment"] is None
    disk = load_bench_dataset("tight", "halles")
    assert disk.name == halles["name"]
    imported_row = next(item for item in datasets if item["id"] == payload["id"])
    assert imported_row["origin"] == "imported"
    assert imported_row["comment"] == "note banc"
    assert imported_row["manual"]["global"] == 7.3
    generated_ref = generated.json()["published"]["salle"]["versions"]["minimal"]["engine_ref"]
    last_run = imported_row["by_ref"][generated_ref]["minimal"]
    assert last_run is not None
    assert last_run["run_id"]

    exported = client.get(
        "/v1/admin/bench/export",
        headers=admin_headers,
        params={"scope": "dataset", "category": "imported", "dataset_id": payload["id"]},
    )
    assert exported.status_code == 200
    pack = exported.json()["datasets"][0]
    assert pack["category"] == "imported"
    assert pack["id"] == payload["id"]
    assert pack["context"]["name"] == "Chez Import"
    assert all("invite_token" not in person for person in pack["context"]["employees"])

    cuisine_token, cuisine_rid = _register_company(client, cuisine_email, password)
    cuisine_headers = _bearer(cuisine_token)
    cuisine_fiche = f"karim-{secrets.token_hex(4)}"
    cuisine_patched = client.patch(
        "/v1/context",
        headers=cuisine_headers,
        json=_cuisine_patch(cuisine_fiche, "Chez Cuisine"),
    )
    assert cuisine_patched.status_code == 200
    assert cuisine_patched.json()["ready"]["cuisine"] is True
    cuisine_import = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": cuisine_rid, "include_salle": False, "include_cuisine": True},
    )
    assert cuisine_import.status_code == 200
    cuisine_id = cuisine_import.json()["id"]
    blocked = client.post(
        "/v1/admin/bench/run",
        headers=admin_headers,
        json={"scope": "dataset", "category": "imported", "dataset_id": cuisine_id, "search_effort": "minimal"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"] == DETAIL_NO_SALLE
