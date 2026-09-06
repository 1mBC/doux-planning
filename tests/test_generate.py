from __future__ import annotations

import os
import secrets
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.app import app
from doux_planning.api.db import Company, reset_engine, session_scope
from doux_planning.types import WEEKDAYS


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_generate_schema():
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


def _slot(team_blob: dict | None, effort: str | None = None) -> dict:
    assert team_blob is not None
    if "versions" in team_blob:
        key = effort or team_blob["latest"]
        cycle = team_blob["versions"][key]
        assert cycle is not None
        return cycle
    return team_blob


def _assert_live_recap(cycle: dict) -> None:
    assert cycle["stats"]["assignments"] == len(cycle["assignments"])
    assert cycle["legal_rows"]
    assert cycle["legal_cols"]
    assert cycle["wish_cols"]
    assert cycle["wish_rows"]
    wish_keys = {col["key"] for col in cycle["wish_cols"]}
    assert "we1j" not in wish_keys
    assert "weA" not in wish_keys
    assert "weB" not in wish_keys


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


def test_generate_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    headers = _bearer("x")
    cycles = client.get("/v1/cycles", headers=headers)
    assert cycles.status_code == 503
    assert cycles.json()["detail"] == "Base indisponible."
    generate = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generate.status_code == 503
    assert generate.json()["detail"] == "Base indisponible."
    job = client.get("/v1/generate/jobs/x", headers=headers)
    assert job.status_code == 503
    assert job.json()["detail"] == "Base indisponible."
    maximal = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "maximal"},
    )
    assert maximal.status_code == 503
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    assert client.post("/v1/sandbox/enter").status_code == 200


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_generate_persist_cycles_auth_and_example():
    client = _client()
    email = f"gen-{secrets.token_hex(4)}@example.com"
    password = "password1"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    headers = _bearer(token)

    empty = client.get("/v1/cycles", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {"published": {"salle": None, "cuisine": None}}

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    assert patched.json()["ready"]["salle"] is True
    assert patched.json()["ready"]["cuisine"] is False
    company_code = patched.json()["company_code"]

    first = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["team"] == "salle"
    assert body["search_effort"] == "minimal"
    salle = body["published"]["salle"]
    assert salle is not None
    assert salle["latest"] == "minimal"
    assert salle["versions"]["optimized"] is None
    assert salle["versions"]["maximal"] is None
    cycle = _slot(salle, "minimal")
    assert cycle["assignments"]
    assert cycle["search_effort"] == "minimal"
    assert cycle["generated_at"]
    assert isinstance(cycle["duration_seconds"], (int, float))
    assert cycle["duration_seconds"] >= 0
    assert all(shift["team"] == "salle" for shift in cycle["assignments"])
    assert all(
        set(shift)
        >= {
            "employee_id",
            "day_index",
            "weekday",
            "service_id",
            "team",
            "start_minutes",
            "end_minutes",
            "post_level",
            "duration_hours",
        }
        for shift in cycle["assignments"]
    )
    assert "legal_rows" not in body
    assert "stats" not in body
    _assert_live_recap(cycle)
    assert body["published"]["cuisine"] is None

    with patch("doux_planning.context.generate_cycle") as solve:
        cuisine = client.post(
            "/v1/generate",
            headers=headers,
            json={"team": "cuisine", "search_effort": "minimal"},
        )
    assert cuisine.status_code == 409
    assert cuisine.json()["detail"] == "Cette équipe n'est pas prête à calculer."
    solve.assert_not_called()
    after_conflict = client.get("/v1/cycles", headers=headers)
    assert after_conflict.status_code == 200
    assert _slot(after_conflict.json()["published"]["salle"], "minimal")["assignments"]
    assert after_conflict.json()["published"]["cuisine"] is None

    second = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert second.status_code == 200
    second_cycle = _slot(second.json()["published"]["salle"], "minimal")
    assert second_cycle["assignments"]
    assert all(shift["team"] == "salle" for shift in second_cycle["assignments"])
    _assert_live_recap(second_cycle)
    assert second.json()["published"]["cuisine"] is None

    published = second.json()["published"]
    reset_engine()
    again = client.get("/v1/cycles", headers=headers)
    assert again.status_code == 200
    assert again.json() == {"published": published}

    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        salle_blob = company.published_cycles["salle"]
        minimal = salle_blob["versions"]["minimal"]
        company.published_cycles = {
            "salle": {"assignments": minimal["assignments"], "warnings": minimal["warnings"]},
            "cuisine": None,
        }
        flag_modified(company, "published_cycles")
    reset_engine()
    hydrated = client.get("/v1/cycles", headers=headers)
    assert hydrated.status_code == 200
    assert hydrated.json()["published"]["cuisine"] is None
    coerced = hydrated.json()["published"]["salle"]
    assert coerced["latest"] == "optimized"
    assert coerced["versions"]["minimal"] is None
    _assert_live_recap(_slot(coerced, "optimized"))
    assert _slot(coerced, "optimized")["assignments"] == _slot(published["salle"], "minimal")["assignments"]

    invalid = client.post("/v1/generate", headers=headers, json={"team": "bar", "search_effort": "minimal"})
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Champs invalides."

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
    emp_headers = _bearer(employee.json()["token"])
    forbidden_gen = client.post(
        "/v1/generate",
        headers=emp_headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert forbidden_gen.status_code == 403
    assert forbidden_gen.json()["detail"] == "Action réservée au restaurateur."
    forbidden_cycles = client.get("/v1/cycles", headers=emp_headers)
    assert forbidden_cycles.status_code == 403
    assert forbidden_cycles.json()["detail"] == "Action réservée au restaurateur."

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    with_session = client.get("/v1/examples/saint-cloud", headers=headers)
    assert with_session.status_code == 200
    assert with_session.json()["planning"]["stats"]["assignments"] == 92

    context = client.get("/v1/context", headers=headers)
    assert context.status_code == 200
    assert context.json()["ready"]["salle"] is True
    logged = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert logged.status_code == 200
    login_token = logged.json()["token"]
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 200
    assert client.post("/v1/auth/logout", headers=_bearer(login_token)).status_code == 204
    assert client.get("/v1/me", headers=_bearer(login_token)).status_code == 401


def _stub_generate_team(state, team, search):
    from doux_planning.context import TeamNotReady, expand_typical_week, team_ready
    from doux_planning.engine import EngineResult, PlanningDraft
    from doux_planning.planning import PublishedCycle
    from doux_planning.staff import default_legal_rules

    if not team_ready(state, team):
        raise TeamNotReady(team)
    draft = PlanningDraft(
        employees=tuple(person for person in state.employees if person.team == team),
        structures=tuple(item for item in expand_typical_week(state) if item.team == team),
        hours=state.hours,
        legal_rules=default_legal_rules(),
        search_effort=search,
    )
    result = EngineResult(assignments=(), warnings=())
    state.published_cycles[team] = PublishedCycle(id=team.value, draft=draft.with_assignments(()), result=result)
    return state


def _count_rows(model, **filters) -> int:
    from sqlalchemy import func, select

    with session_scope() as session:
        stmt = select(func.count()).select_from(model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)
        return int(session.scalar(stmt) or 0)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_generate_maximal_job_tick_stub_and_auth(capsys):
    from doux_planning.api.db import GenerateJob, GenerateLog
    from doux_planning.api.worker import tick_generate_job

    client = _client()
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"job-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    restaurant_id = registered.json()["me"]["restaurant_id"]
    headers = _bearer(token)
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    assert patched.json()["ready"]["salle"] is True
    company_code = patched.json()["company_code"]

    logs_before = _count_rows(GenerateLog)
    minimal = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert minimal.status_code == 200
    assert _slot(minimal.json()["published"]["salle"], "minimal")["assignments"]
    assert _count_rows(GenerateLog) == logs_before + 1

    with patch("doux_planning.api.generate.generate_team") as solve:
        maximal = client.post(
            "/v1/generate",
            headers=headers,
            json={"team": "salle", "search_effort": "maximal"},
        )
    assert maximal.status_code == 202
    solve.assert_not_called()
    queued = maximal.json()
    assert queued["team"] == "salle"
    assert queued["search_effort"] == "maximal"
    assert queued["status"] == "queued"
    assert queued["estimated_seconds"] == 600
    assert "published" not in queued
    job_id = queued["job_id"]
    assert job_id

    polled = client.get(f"/v1/generate/jobs/{job_id}", headers=headers)
    assert polled.status_code == 200
    assert polled.json()["status"] == "queued"
    assert polled.json()["estimated_seconds"] == 600
    assert "published" not in polled.json()

    again = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "maximal"},
    )
    assert again.status_code == 409
    assert again.json()["detail"] == "Un calcul maximal est déjà en cours."
    assert _count_rows(GenerateJob, restaurant_id=restaurant_id) == 1

    cuisine = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "cuisine", "search_effort": "maximal"},
    )
    assert cuisine.status_code == 409
    assert cuisine.json()["detail"] == "Cette équipe n'est pas prête à calculer."
    assert _count_rows(GenerateJob, restaurant_id=restaurant_id, team="cuisine") == 0

    logs_before_tick = _count_rows(GenerateLog)
    processed = tick_generate_job(generate_team_fn=_stub_generate_team)
    logged = capsys.readouterr().out
    assert "generate start" in logged
    assert "status=done" in logged
    assert processed == job_id
    done = client.get(f"/v1/generate/jobs/{job_id}", headers=headers)
    assert done.status_code == 200
    assert done.json()["status"] == "done"
    assert done.json()["published"]["salle"] is not None
    assert done.json()["published"]["salle"]["latest"] == "maximal"
    assert "assignments" in _slot(done.json()["published"]["salle"], "maximal")
    assert _slot(done.json()["published"]["salle"], "maximal")["duration_seconds"] >= 0
    assert done.json()["published"]["cuisine"] is None
    assert _count_rows(GenerateLog) == logs_before_tick + 1

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
    emp = _bearer(employee.json()["token"])
    assert client.get(f"/v1/generate/jobs/{job_id}", headers=emp).status_code == 403
    assert (
        client.post("/v1/generate", headers=emp, json={"team": "salle", "search_effort": "maximal"}).status_code
        == 403
    )

    other = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"other-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert other.status_code == 201
    foreign = client.get(f"/v1/generate/jobs/{job_id}", headers=_bearer(other.json()["token"]))
    assert foreign.status_code == 404
    missing = client.get("/v1/generate/jobs/inconnu", headers=headers)
    assert missing.status_code == 404
    assert client.get("/v1/generate/jobs/inconnu").status_code == 401

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_generate_versions_slots_me_planning_and_enter():
    from doux_planning.api.db import Company, session_scope
    from doux_planning.context import generate_team
    from doux_planning.types import SearchEffort

    client = _client()
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"ver-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert registered.status_code == 201
    headers = _bearer(registered.json()["token"])
    restaurant_id = registered.json()["me"]["restaurant_id"]
    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    company_code = patched.json()["company_code"]

    first = client.post("/v1/generate", headers=headers, json={"team": "salle", "search_effort": "minimal"})
    assert first.status_code == 200
    minimal_cycle = _slot(first.json()["published"]["salle"], "minimal")
    assert first.json()["published"]["salle"]["latest"] == "minimal"

    def _as_minimal(state, team, search):
        return generate_team(state, team, SearchEffort.MINIMAL)

    with patch("doux_planning.api.generate.generate_team", side_effect=_as_minimal):
        second = client.post(
            "/v1/generate",
            headers=headers,
            json={"team": "salle", "search_effort": "optimized"},
        )
    assert second.status_code == 200
    salle = second.json()["published"]["salle"]
    assert salle["latest"] == "optimized"
    assert _slot(salle, "minimal")["assignments"] == minimal_cycle["assignments"]
    assert _slot(salle, "minimal")["generated_at"] == minimal_cycle["generated_at"]
    optimized_cycle = _slot(salle, "optimized")
    assert optimized_cycle["search_effort"] == "optimized"
    assert optimized_cycle["generated_at"]
    assert optimized_cycle["generated_at"] != minimal_cycle["generated_at"]
    assert isinstance(optimized_cycle["duration_seconds"], (int, float))
    assert optimized_cycle["duration_seconds"] >= 0
    assert salle["versions"]["maximal"] is None

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
    planning = client.get("/v1/me/planning", headers=_bearer(employee.json()["token"]))
    assert planning.status_code == 200
    assert planning.json()["assignments"] == optimized_cycle["assignments"]

    entered_latest = client.post("/v1/live/sandbox/salle/enter", headers=headers)
    assert entered_latest.status_code == 200
    assert entered_latest.json()["planning"]["assignments"] == optimized_cycle["assignments"]

    entered_min = client.post(
        "/v1/live/sandbox/salle/enter",
        headers=headers,
        json={"search_effort": "minimal"},
    )
    assert entered_min.status_code == 200
    assert entered_min.json()["planning"]["assignments"] == minimal_cycle["assignments"]

    published = client.post("/v1/live/sandbox/salle/publish", headers=headers)
    assert published.status_code == 200
    after = published.json()["published"]["salle"]
    assert after["latest"] == "optimized"
    assert _slot(after, "optimized")["assignments"] == optimized_cycle["assignments"]
    assert _slot(after, "optimized")["generated_at"] == optimized_cycle["generated_at"]
    assert _slot(after, "optimized")["duration_seconds"] == optimized_cycle["duration_seconds"]
    assert _slot(after, "minimal")["generated_at"] == minimal_cycle["generated_at"]

    with session_scope() as session:
        company = session.get(Company, restaurant_id)
        assert company is not None
        flat = _slot(first.json()["published"]["salle"], "minimal")
        company.published_cycles = {
            "salle": {"assignments": flat["assignments"], "warnings": flat["warnings"]},
            "cuisine": None,
        }
        flag_modified(company, "published_cycles")
    coerced = client.get("/v1/cycles", headers=headers)
    assert coerced.status_code == 200
    assert coerced.json()["published"]["salle"]["latest"] == "optimized"
    assert "assignments" not in coerced.json()["published"]["salle"]
    assert _slot(coerced.json()["published"]["salle"], "optimized")["assignments"] == flat["assignments"]
    assert "duration_seconds" not in _slot(coerced.json()["published"]["salle"], "optimized")

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
