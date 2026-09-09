from __future__ import annotations

import os
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, promote_admin_email
from doux_planning.api.db import BenchRun, GenerateLog, reset_engine, session_scope
from doux_planning.bench import BenchOutcome, list_bench_datasets, load_bench_dataset, run_bench
from doux_planning.context import SCORE_WEIGHTS, CycleScore, ScoreNotes, cycle_score, empty_restaurant, team_ready, upsert_employee
from doux_planning.engine import PlanningDraft, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import SearchEffort, Team, WEEKDAYS, WarningSeverity
from tests.fixtures import employee


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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


def _salle_patch(fiche_id: str) -> dict:
    return {
        "name": "Chez Bench",
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


def _stub_run_bench(category, dataset_id, effort):
    notes = ScoreNotes(10.0, 10.0, 10.0, None, 10.0)
    score = CycleScore(notes=notes, weights=dict(SCORE_WEIGHTS), global_score=10.0)
    return BenchOutcome(
        category=category,
        id=dataset_id,
        search_effort=effort,
        duration_seconds=0.0,
        assignments=(),
        warnings=(),
        score=score,
        expected_score=score,
        deltas={"couverture": 0.0, "legal": 0.0, "contrat": 0.0, "wellbeing": None, "roles": 0.0, "global": 0.0},
    )


def _count_rows(model) -> int:
    with session_scope() as db:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _expected_result(dataset):
    staff = tuple(person for person in dataset.state.employees if person.team == Team.SALLE)
    structures = tuple(item for item in dataset.state.structures if item.team == Team.SALLE)
    draft = PlanningDraft(
        employees=staff,
        structures=structures,
        hours=dataset.state.hours,
        assignments=dataset.expected,
        legal_rules=default_legal_rules(),
    )
    return evaluate(draft)


FROZEN_BENCH_PAIRS = {
    ("tight", "halles"),
    ("clock", "nocturne"),
    ("wishes", "campus"),
    ("ladder", "brigade"),
    ("crafted", "atelier"),
    ("crafted", "rivoli"),
    ("crafted", "marais"),
}


def test_list_bench_datasets_has_seven_salle_games():
    listed = list_bench_datasets()
    assert [(item.category, item.id) for item in listed] == [
        ("tight", "halles"),
        ("clock", "nocturne"),
        ("wishes", "campus"),
        ("ladder", "brigade"),
        ("crafted", "atelier"),
        ("crafted", "marais"),
        ("crafted", "rivoli"),
    ]
    assert {(item.category, item.id) for item in listed} == FROZEN_BENCH_PAIRS
    assert all(item.name and item.challenge_fr for item in listed)


def test_load_halles_is_salle_ready_not_cuisine():
    dataset = load_bench_dataset("tight", "halles")
    assert team_ready(dataset.state, Team.SALLE)
    assert not team_ready(dataset.state, Team.CUISINE)
    assert all(person.invite_token != person.id for person in dataset.state.employees)


def test_expected_assignments_have_zero_interdit():
    for item in list_bench_datasets():
        dataset = load_bench_dataset(item.category, item.id)
        result = _expected_result(dataset)
        assert result.of_severity(WarningSeverity.INTERDIT) == ()


@pytest.mark.parametrize("dataset_id", ["atelier", "rivoli", "marais"])
def test_crafted_expected_global_at_least_nine_five(dataset_id):
    dataset = load_bench_dataset("crafted", dataset_id)
    result = _expected_result(dataset)
    score = cycle_score(
        PlanningDraft(
            employees=tuple(person for person in dataset.state.employees if person.team == Team.SALLE),
            structures=tuple(item for item in dataset.state.structures if item.team == Team.SALLE),
            hours=dataset.state.hours,
            assignments=dataset.expected,
            legal_rules=default_legal_rules(),
        ),
        result,
    )
    assert score.global_score is not None
    assert score.global_score >= 9.5


def test_run_bench_tight_halles_minimal_has_scores_and_deltas():
    outcome = run_bench("tight", "halles", SearchEffort.MINIMAL)
    assert outcome.category == "tight"
    assert outcome.id == "halles"
    assert outcome.search_effort == SearchEffort.MINIMAL
    assert outcome.score is not None
    assert outcome.expected_score is not None
    assert set(outcome.deltas) == {"couverture", "legal", "contrat", "wellbeing", "roles", "global"}


def test_run_bench_leaves_live_restaurant_unchanged():
    state = empty_restaurant("resto-live")
    upsert_employee(state, employee("Sam", "commis", hours=35, employee_id="sam"))
    before = (
        state.identity,
        tuple(state.employees),
        tuple(state.structures),
        state.hours,
        state.cycle,
        dict(state.published_cycles),
        dict(state.live_sandboxes),
        tuple(state.service_types),
        state.typical_week,
        dict(state.ladders),
        state.company_services,
    )
    run_bench("tight", "halles", SearchEffort.MINIMAL)
    after = (
        state.identity,
        tuple(state.employees),
        tuple(state.structures),
        state.hours,
        state.cycle,
        dict(state.published_cycles),
        dict(state.live_sandboxes),
        tuple(state.service_types),
        state.typical_week,
        dict(state.ladders),
        state.company_services,
    )
    assert after == before
    assert state.published_cycles == {Team.SALLE: None, Team.CUISINE: None}


def test_admin_bench_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    listed = client.get("/v1/admin/bench/datasets", headers=_bearer("x"))
    assert listed.status_code == 503
    assert listed.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_bench_http_runs_jobs_compare_and_resto_generate(monkeypatch):
    from doux_planning.api.worker import tick_bench_job

    client = _client()
    password = "password1"
    email = f"bench-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    other = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"user-{secrets.token_hex(4)}@example.com", "password": password},
    )
    assert other.status_code == 201
    forbidden = client.post(
        "/v1/admin/bench/run",
        headers=_bearer(other.json()["token"]),
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "minimal"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == DETAIL_ADMIN

    monkeypatch.setenv("ADMIN_EMAIL", email)
    promote_admin_email()
    assert client.get("/v1/me", headers=headers).json()["admin"] is True

    datasets = client.get("/v1/admin/bench/datasets", headers=headers)
    assert datasets.status_code == 200
    assert datasets.json()["app_version"] == "0.27.0"
    assert {(item["category"], item["id"]) for item in datasets.json()["datasets"]} == FROZEN_BENCH_PAIRS

    logs_before = _count_rows(GenerateLog)
    runs_before = _count_rows(BenchRun)
    posted = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "minimal"},
    )
    assert posted.status_code == 200
    summaries = posted.json()["runs"]
    assert len(summaries) == 1
    first = summaries[0]
    assert first["category"] == "tight"
    assert first["dataset_id"] == "halles"
    assert first["search_effort"] == "minimal"
    assert first["app_version"] == "0.27.0"
    assert "notes" in first["score"] and "resumes" not in first["score"]
    assert "assignments" not in first
    assert _count_rows(GenerateLog) == logs_before
    assert _count_rows(BenchRun) == runs_before + 1

    listed = client.get("/v1/admin/bench/runs", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == first["id"] for item in listed.json()["runs"])
    halles = client.get("/v1/admin/bench/runs", headers=headers, params={"category": "tight", "dataset_id": "halles"})
    assert halles.status_code == 200
    assert all(item["dataset_id"] == "halles" for item in halles.json()["runs"])

    compared = client.get("/v1/admin/bench/compare/tight/halles/minimal", headers=headers)
    assert compared.status_code == 200
    assert compared.json()["id"] == first["id"]
    assert compared.json()["expected"]["assignments"]
    assert compared.json()["expected"]["score"] == first["expected_score"]
    assert compared.json()["assignments"] is not None
    assert "facts" in compared.json()
    assert "warnings" not in compared.json()
    assert "resumes" not in compared.json()["score"]

    queued = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "all", "search_effort": "maximal"},
    )
    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    job_ids = queued.json()["job_ids"]
    assert len(job_ids) == 7
    runs_before_tick = _count_rows(BenchRun)
    remaining = set(job_ids)
    for _ in range(40):
        if not remaining:
            break
        job_id = tick_bench_job(run_bench_fn=_stub_run_bench)
        assert job_id is not None
        remaining.discard(job_id)
    assert not remaining
    assert _count_rows(GenerateLog) == logs_before
    run_ids = []
    for job_id in job_ids:
        done = client.get(f"/v1/admin/bench/jobs/{job_id}", headers=headers)
        assert done.status_code == 200
        assert done.json()["status"] == "done"
        assert done.json()["run_id"]
        run_ids.append(done.json()["run_id"])
    assert len(set(run_ids)) == 7
    assert _count_rows(BenchRun) >= runs_before_tick + 7
    crafted = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "category", "category": "crafted", "search_effort": "maximal"},
    )
    assert crafted.status_code == 202
    assert crafted.json()["status"] == "queued"
    assert len(crafted.json()["job_ids"]) == 3
    maximal = client.get("/v1/admin/bench/compare/tight/halles/maximal", headers=headers)
    assert maximal.status_code == 200
    assert maximal.json()["search_effort"] == "maximal"

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    generated = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    assert generated.json()["published"]["salle"]["versions"]["minimal"]["assignments"]
    assert _count_rows(GenerateLog) == logs_before + 1

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
