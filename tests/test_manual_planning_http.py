from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.app import app
from doux_planning.api.db import Company, GenerateLog, reset_engine, session_scope
from doux_planning.api.generate import SLOT_KEYS, compute_latest, normalize_team_published
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_manual_schema():
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


def _salle_patch(fiche_id: str, name: str = "Chez Manuel") -> dict:
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


def _assert_four_slots(pack: dict) -> None:
    assert pack is not None
    assert set(pack["versions"]) == set(SLOT_KEYS)
    for key in SLOT_KEYS:
        assert key in pack["versions"]


def _count_logs() -> int:
    from sqlalchemy import func, select

    with session_scope() as session:
        return int(session.scalar(select(func.count()).select_from(GenerateLog)) or 0)


def test_bench_and_generate_efforts_stay_three_computes():
    from doux_planning.api.bench import EFFORTS as BENCH_EFFORTS
    from doux_planning.api.generate import EFFORTS

    assert EFFORTS == ("minimal", "optimized", "maximal")
    assert BENCH_EFFORTS == ("minimal", "optimized", "maximal")
    assert SLOT_KEYS == ("minimal", "optimized", "maximal", "manuel")
    assert "manuel" not in EFFORTS
    assert "manuel" not in BENCH_EFFORTS


def test_normalize_three_key_blob_adds_manuel_null():
    blob = {
        "versions": {"minimal": None, "optimized": {"assignments": [{"employee_id": "e"}]}, "maximal": None},
        "latest": "optimized",
    }
    pack, dirty = normalize_team_published(blob)
    assert dirty is True
    _assert_four_slots(pack)
    assert pack["versions"]["manuel"] is None
    assert pack["versions"]["optimized"]["assignments"] == [{"employee_id": "e"}]
    assert pack["latest"] == "optimized"


def test_normalize_flat_cycle_becomes_optimized_plus_manuel_null():
    pack, dirty = normalize_team_published({"assignments": [{"employee_id": "e"}]})
    assert dirty is True
    _assert_four_slots(pack)
    assert pack["latest"] == "optimized"
    assert pack["versions"]["minimal"] is None
    assert pack["versions"]["maximal"] is None
    assert pack["versions"]["manuel"] is None
    assert pack["versions"]["optimized"]["search_effort"] == "optimized"
    assert pack["versions"]["optimized"]["assignments"] == [{"employee_id": "e"}]


def test_compute_latest_tie_break_manuel_then_newer_generate():
    stamp = "2026-09-21T12:00:00+00:00"
    versions = {
        "minimal": {"generated_at": stamp},
        "optimized": {"generated_at": stamp},
        "maximal": {"generated_at": stamp},
        "manuel": {"generated_at": stamp},
    }
    assert compute_latest(versions) == "manuel"
    versions["optimized"] = {"generated_at": "2026-09-21T13:00:00+00:00"}
    assert compute_latest(versions) == "optimized"


def test_four_key_blob_is_not_dirty():
    blob = {
        "versions": {"minimal": None, "optimized": {"assignments": []}, "maximal": None, "manuel": None},
        "latest": "optimized",
    }
    pack, dirty = normalize_team_published(blob)
    assert dirty is False
    _assert_four_slots(pack)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_manual_live_enter_fill_publish_generate_and_coerce():
    client = _client()
    email = f"man-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": "password1"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    headers = _bearer(token)
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    assert patched.json()["ready"]["salle"] is True
    assert patched.json()["ready"]["cuisine"] is False

    forbidden = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "manuel"},
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["detail"] == "Champs invalides."

    cuisine = client.post(
        "/v1/live/sandbox/cuisine/enter",
        headers=headers,
        json={"search_effort": "manuel"},
    )
    assert cuisine.status_code == 409
    assert cuisine.json()["detail"] == "Cette équipe n'est pas prête à calculer."

    logs_before = _count_logs()
    entered = client.post(
        "/v1/live/sandbox/salle/enter",
        headers=headers,
        json={"search_effort": "manuel"},
    )
    assert entered.status_code == 200
    body = entered.json()
    assert body["team"] == "salle"
    assert body["planning"]["assignments"] == []
    assert isinstance(body["planning"]["facts"], list)
    assert any(item.get("kind") == "empty_post" for item in body["planning"]["facts"])
    assert body["history"] == []

    cycles = client.get("/v1/cycles", headers=headers)
    assert cycles.status_code == 200
    assert cycles.json()["published"]["salle"] is None
    assert cycles.json()["published"]["cuisine"] is None

    slot = {
        "employee_id": fiche_id,
        "day_index": 0,
        "weekday": "monday",
        "service_id": "midday",
        "team": "salle",
    }
    preview = client.post(
        "/v1/live/sandbox/salle/preview",
        headers=headers,
        json={"gesture": "fill", "slot": slot, "start_minutes": None, "end_minutes": None},
    )
    assert preview.status_code == 200
    proposals = preview.json()["proposals"]
    assert proposals
    first = proposals[0]
    committed = client.post(
        "/v1/live/sandbox/salle/commit",
        headers=headers,
        json={
            "gesture": "fill",
            "slot": slot,
            "employee_id": fiche_id,
            "start_minutes": first["start_minutes"],
            "end_minutes": first["end_minutes"],
        },
    )
    assert committed.status_code == 200
    filled = committed.json()["planning"]["assignments"]
    assert filled
    assert committed.json()["history"]

    discarded = client.post("/v1/live/sandbox/salle/discard", headers=headers)
    assert discarded.status_code == 200
    assert discarded.json()["planning"]["assignments"] == []
    assert discarded.json()["history"] == []
    after_discard = client.get("/v1/cycles", headers=headers)
    assert after_discard.json()["published"]["salle"] is None

    reentered = client.post(
        "/v1/live/sandbox/salle/enter",
        headers=headers,
        json={"search_effort": "manuel"},
    )
    assert reentered.status_code == 200
    preview_again = client.post(
        "/v1/live/sandbox/salle/preview",
        headers=headers,
        json={"gesture": "fill", "slot": slot, "start_minutes": None, "end_minutes": None},
    )
    assert preview_again.status_code == 200
    first = preview_again.json()["proposals"][0]
    committed_again = client.post(
        "/v1/live/sandbox/salle/commit",
        headers=headers,
        json={
            "gesture": "fill",
            "slot": slot,
            "employee_id": fiche_id,
            "start_minutes": first["start_minutes"],
            "end_minutes": first["end_minutes"],
        },
    )
    assert committed_again.status_code == 200
    filled = committed_again.json()["planning"]["assignments"]
    assert filled

    published = client.post("/v1/live/sandbox/salle/publish", headers=headers)
    assert published.status_code == 200
    salle = published.json()["published"]["salle"]
    _assert_four_slots(salle)
    assert salle["latest"] == "manuel"
    manuel = salle["versions"]["manuel"]
    assert manuel is not None
    assert manuel["assignments"] == filled
    assert manuel["search_effort"] == "manuel"
    assert manuel["generated_at"]
    assert "duration_seconds" not in manuel
    assert "engine_ref" not in manuel
    assert salle["versions"]["minimal"] is None
    assert salle["versions"]["optimized"] is None
    assert salle["versions"]["maximal"] is None
    assert published.json()["published"]["cuisine"] is None
    assert _count_logs() == logs_before

    got = client.get("/v1/cycles", headers=headers)
    assert got.status_code == 200
    got_salle = got.json()["published"]["salle"]
    _assert_four_slots(got_salle)
    assert got_salle["latest"] == "manuel"
    assert got_salle["versions"]["manuel"]["assignments"] == filled
    closed = client.get("/v1/live/sandbox/salle", headers=headers)
    assert closed.status_code == 404

    generated = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "optimized"},
    )
    assert generated.status_code == 200
    after = generated.json()["published"]["salle"]
    _assert_four_slots(after)
    assert after["versions"]["manuel"]["assignments"] == filled
    assert after["versions"]["manuel"]["generated_at"] == manuel["generated_at"]
    assert after["versions"]["optimized"] is not None
    assert after["versions"]["optimized"]["search_effort"] == "optimized"
    if after["versions"]["optimized"]["generated_at"] > manuel["generated_at"]:
        assert after["latest"] == "optimized"
    else:
        assert after["latest"] == "manuel"

    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        pack = company.published_cycles["salle"]
        three = {
            "versions": {
                "minimal": pack["versions"]["minimal"],
                "optimized": pack["versions"]["optimized"],
                "maximal": pack["versions"]["maximal"],
            },
            "latest": pack["latest"],
        }
        company.published_cycles = {"salle": three, "cuisine": None}
        flag_modified(company, "published_cycles")
    reset_engine()
    coerced = client.get("/v1/cycles", headers=headers)
    assert coerced.status_code == 200
    coerced_salle = coerced.json()["published"]["salle"]
    _assert_four_slots(coerced_salle)
    assert coerced_salle["versions"]["manuel"] is None
    assert coerced_salle["versions"]["optimized"] is not None
    assert coerced.json()["published"]["cuisine"] is None
    assert _count_logs() == logs_before + 1
