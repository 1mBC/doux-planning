from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, DETAIL_INVALID_FIELDS, promote_admin_email
from doux_planning.api.bench import DETAIL_BENCH_RUN_MISSING
from doux_planning.api.db import BenchRun, reset_engine, session_scope
from doux_planning.bench import engine_ref, list_engine_refs
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_export_speed_schema():
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


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_bench_export_dataset_all_engines_and_versions_origin(monkeypatch):
    client = _client()
    password = "password1"
    admin_email = f"export-speed-admin-{secrets.token_hex(4)}@example.com"
    resto_email = f"export-speed-resto-{secrets.token_hex(4)}@example.com"
    admin_token, _admin_rid = _register_company(client, admin_email, password)
    admin_headers = _promote(client, admin_email, admin_token, monkeypatch)
    other_token, restaurant_id = _register_company(client, resto_email, password)
    other_headers = _bearer(other_token)

    nope = client.get("/v1/admin/bench/versions", headers=admin_headers, params={"origin": "nope"})
    assert nope.status_code == 400
    assert nope.json()["detail"] == DETAIL_INVALID_FIELDS

    forbidden_versions = client.get("/v1/admin/bench/versions", headers=other_headers)
    assert forbidden_versions.status_code == 403
    assert forbidden_versions.json()["detail"] == DETAIL_ADMIN
    forbidden_export = client.get(
        "/v1/admin/bench/export",
        headers=other_headers,
        params={"scope": "dataset", "category": "tight", "dataset_id": "halles"},
    )
    assert forbidden_export.status_code == 403
    assert forbidden_export.json()["detail"] == DETAIL_ADMIN

    with session_scope() as db:
        db.execute(delete(BenchRun).where(BenchRun.category == "shapes", BenchRun.dataset_id == "journee"))
    empty = client.get(
        "/v1/admin/bench/export",
        headers=admin_headers,
        params={"scope": "dataset", "category": "shapes", "dataset_id": "journee"},
    )
    assert empty.status_code == 404
    assert empty.json()["detail"] == DETAIL_BENCH_RUN_MISSING

    current = engine_ref()
    older = next(ref for ref in list_engine_refs() if ref != current)
    monkeypatch.setattr("doux_planning.api.generate.get_effective_engine_ref", lambda: older)

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=other_headers, json=_salle_patch(fiche_id, "Chez Export Speed"))
    assert patched.status_code == 200
    generated = client.post(
        "/v1/generate",
        headers=other_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    slot = generated.json()["published"]["salle"]["versions"]["minimal"]
    assert slot["engine_ref"] == older
    assert older != current

    imported = client.post(
        "/v1/admin/bench/import",
        headers=admin_headers,
        json={"restaurant_id": restaurant_id, "include_runs": True, "comment": "export speed"},
    )
    assert imported.status_code == 200
    imported_id = imported.json()["id"]
    assert imported.json()["category"] == "imported"

    exported = client.get(
        "/v1/admin/bench/export",
        headers=admin_headers,
        params={"scope": "dataset", "category": "imported", "dataset_id": imported_id},
    )
    assert exported.status_code == 200
    pack = exported.json()
    assert pack["kind"] == "bench-pack"
    assert pack["scope"] == "dataset"
    assert len(pack["datasets"]) == 1
    efforts = pack["datasets"][0]["efforts"]
    assert efforts
    assert any(item["engine_ref"] != current for item in efforts)
    assert any(item["engine_ref"] == older for item in efforts)
    assert any(item.get("trace") is None for item in efforts)

    registre = list(list_engine_refs())
    imported_versions = client.get(
        "/v1/admin/bench/versions",
        headers=admin_headers,
        params={"origin": "imported"},
    )
    assert imported_versions.status_code == 200
    imported_datasets = imported_versions.json()["datasets"]
    assert imported_datasets
    assert all(item["origin"] == "imported" for item in imported_datasets)
    assert all(item["category"] == "imported" for item in imported_datasets)
    assert imported_id in {item["id"] for item in imported_datasets}
    assert imported_versions.json()["engine_refs"][: len(registre)] == registre

    catalogue_versions = client.get(
        "/v1/admin/bench/versions",
        headers=admin_headers,
        params={"origin": "catalogue"},
    )
    assert catalogue_versions.status_code == 200
    catalogue_datasets = catalogue_versions.json()["datasets"]
    assert catalogue_datasets
    assert all(item["origin"] == "catalogue" for item in catalogue_datasets)
    assert all(item["category"] != "imported" for item in catalogue_datasets)
    assert imported_id not in {item["id"] for item in catalogue_datasets}
    assert any(item["category"] == "tight" and item["id"] == "halles" for item in catalogue_datasets)
    assert catalogue_versions.json()["engine_refs"][: len(registre)] == registre

    both = client.get("/v1/admin/bench/versions", headers=admin_headers)
    assert both.status_code == 200
    origins = {item["origin"] for item in both.json()["datasets"]}
    assert origins == {"catalogue", "imported"}
    assert imported_id in {item["id"] for item in both.json()["datasets"]}
    assert any(item["category"] == "tight" and item["id"] == "halles" for item in both.json()["datasets"])
    assert both.json()["engine_refs"][: len(registre)] == registre
