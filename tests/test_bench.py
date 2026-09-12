from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, promote_admin_email
from doux_planning.api.db import BenchRun, GenerateLog, reset_engine, session_scope
from doux_planning.bench import BenchOutcome, engine_ref, list_bench_datasets, load_bench_dataset, run_bench
from doux_planning.context import (
    SCORE_WEIGHTS,
    CycleScore,
    ScoreNotes,
    cycle_score,
    empty_restaurant,
    team_ready,
    upsert_employee,
)
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
        facts=(),
        expected_facts=(),
        score=score,
        expected_score=score,
        deltas={"couverture": 0.0, "legal": 0.0, "contrat": 0.0, "wellbeing": None, "roles": 0.0, "global": 0.0},
        engine_ref="core-1",
    )


def _count_rows(model) -> int:
    with session_scope() as db:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _insert_bench_run(
    *,
    app_version: str,
    category: str,
    dataset_id: str,
    search_effort: str,
    score_global: float,
    expected_global: float,
) -> str:
    run_id = secrets.token_urlsafe(12)
    with session_scope() as db:
        db.add(
            BenchRun(
                id=run_id,
                created_at=datetime.now(timezone.utc),
                app_version=app_version,
                category=category,
                dataset_id=dataset_id,
                search_effort=search_effort,
                duration_seconds=0.0,
                score={"notes": {}, "global": score_global, "weights": {}},
                expected_score={"notes": {}, "global": expected_global, "weights": {}},
                deltas={"global": score_global - expected_global},
                assignments=[],
                warnings=[],
            )
        )
    return run_id


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
    assert outcome.facts
    assert outcome.expected_facts
    assert all(
        fact.severity is not WarningSeverity.INTERDIT
        for fact in outcome.expected_facts
        if fact.polarity == "miss"
    )
    assert any(
        fact.polarity == "hit" and fact.kind in {"post_held", "role_gap"}
        for fact in (*outcome.facts, *outcome.expected_facts)
    )
    assert outcome.engine_ref == "core-2"


def test_engine_ref_is_core_two():
    assert engine_ref() == "core-2"


def test_run_bench_atelier_minimal_fewer_saturday_evening_empties():
    outcome = run_bench("crafted", "atelier", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-2"
    saturday_evening_empties = [
        fact
        for fact in outcome.facts
        if fact.polarity == "miss"
        and fact.kind == "empty_post"
        and fact.payload.get("weekday") == "saturday"
        and fact.payload.get("service_id") == "evening"
    ]
    assert len(saturday_evening_empties) < 4


def test_run_bench_marais_minimal_hard_max_evenings():
    outcome = run_bench("crafted", "marais", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-2"
    assert not any(fact.polarity == "miss" and fact.kind == "max_evenings" for fact in outcome.facts)
    assert not any(shift.employee_id == "e" and shift.service_id == "evening" for shift in outcome.assignments)


def test_run_bench_rivoli_minimal_expected_zero_interdit():
    outcome = run_bench("crafted", "rivoli", SearchEffort.MINIMAL)
    assert all(
        fact.severity is not WarningSeverity.INTERDIT
        for fact in outcome.expected_facts
        if fact.polarity == "miss"
    )


def test_run_bench_campus_minimal_runs():
    outcome = run_bench("wishes", "campus", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-2"
    assert outcome.search_effort == SearchEffort.MINIMAL


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
    assert datasets.json()["engine_ref"] == datasets.json()["app_version"] == "core-0"
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
    assert first["engine_ref"] == first["app_version"] == "core-0"
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
    assert compared.json()["employees"]
    assert all("name" in person and "id" in person for person in compared.json()["employees"])
    model_facts = compared.json()["model"]["facts"]
    manual_facts = compared.json()["manual"]["facts"]
    assert any(item.get("polarity") == "hit" for item in model_facts)
    assert any(item.get("polarity") == "hit" for item in manual_facts)
    assert "facts" not in compared.json()
    assert "assignments" not in compared.json()
    assert "expected" not in compared.json()
    assert "warnings" not in compared.json()
    assert "resumes" not in compared.json()["score"]
    assert "resumes" not in compared.json()["model"]["score"]

    exported = client.get(
        "/v1/admin/bench/export",
        headers=headers,
        params={"scope": "dataset", "category": "tight", "dataset_id": "halles"},
    )
    assert exported.status_code == 200
    pack = exported.json()
    assert pack["export_version"] == 1
    assert pack["kind"] == "bench-pack"
    assert pack["scope"] == "dataset"
    assert pack["engine_ref"] == pack["app_version"] == "core-0"
    assert pack["exported_at"]
    assert len(pack["datasets"]) == 1
    halles_pack = pack["datasets"][0]
    assert halles_pack["category"] == "tight"
    assert halles_pack["id"] == "halles"
    assert halles_pack["context"]
    assert all("invite_token" not in person for person in halles_pack["context"]["employees"])
    assert halles_pack["manual"]["facts"]
    assert halles_pack["efforts"][0]["search_effort"] == "minimal"
    assert halles_pack["efforts"][0]["run_id"] == first["id"]
    assert halles_pack["efforts"][0]["engine_ref"] == "core-0"
    assert "below_manuel" in halles_pack["efforts"][0]
    assert halles_pack["efforts"][0]["model"]["facts"]

    below = client.get("/v1/admin/bench/export", headers=headers, params={"scope": "below_manuel"})
    assert below.status_code == 200
    assert below.json()["kind"] == "bench-pack"
    assert below.json()["scope"] == "below_manuel"
    assert isinstance(below.json()["datasets"], list)

    forbidden_export = client.get(
        "/v1/admin/bench/export",
        headers=_bearer(other.json()["token"]),
        params={"scope": "below_manuel"},
    )
    assert forbidden_export.status_code == 403
    assert forbidden_export.json()["detail"] == DETAIL_ADMIN

    by_id = client.get(f"/v1/admin/bench/runs/{first['id']}", headers=headers)
    assert by_id.status_code == 200
    assert by_id.json()["id"] == first["id"]
    assert by_id.json()["engine_ref"] == by_id.json()["app_version"] == "core-0"
    assert "model" in by_id.json() and "manual" in by_id.json()
    assert any(item.get("polarity") == "hit" for item in by_id.json()["model"]["facts"])
    assert any(item.get("polarity") == "hit" for item in by_id.json()["manual"]["facts"])
    assert "assignments" not in by_id.json()
    assert "facts" not in by_id.json()
    missing_run = client.get("/v1/admin/bench/runs/unknown-run", headers=headers)
    assert missing_run.status_code == 404

    _insert_bench_run(
        app_version="core-1",
        category="tight",
        dataset_id="halles",
        search_effort="minimal",
        score_global=1.0,
        expected_global=8.0,
    )
    versions = client.get("/v1/admin/bench/versions", headers=headers)
    assert versions.status_code == 200
    assert versions.json()["engine_ref"] == "core-0"
    assert "core-0" in versions.json()["engine_refs"]
    assert "core-1" in versions.json()["engine_refs"]
    assert "0.27.0" not in versions.json()["engine_refs"]
    halles_row = next(item for item in versions.json()["datasets"] if item["id"] == "halles")
    assert set(halles_row["by_ref"]) >= {"core-0", "core-1"}
    assert halles_row["by_ref"]["core-0"]["minimal"]["run_id"] == first["id"]
    assert halles_row["by_ref"]["core-1"]["minimal"]["run_id"]
    assert halles_row["by_ref"]["core-1"]["minimal"]["run_id"] != first["id"]
    assert set(halles_row["by_ref"]["core-0"]) == {"minimal", "optimized", "maximal"}
    current_compare = client.get("/v1/admin/bench/compare/tight/halles/minimal", headers=headers)
    assert current_compare.status_code == 200
    assert current_compare.json()["id"] == first["id"]
    assert current_compare.json()["engine_ref"] == "core-0"

    legacy_id = _insert_bench_run(
        app_version="0.27.0",
        category="clock",
        dataset_id="nocturne",
        search_effort="minimal",
        score_global=4.0,
        expected_global=7.0,
    )
    legacy = client.get(f"/v1/admin/bench/runs/{legacy_id}", headers=headers)
    assert legacy.status_code == 200
    assert legacy.json()["engine_ref"] == legacy.json()["app_version"] == "core-0"
    merged = client.get("/v1/admin/bench/versions", headers=headers)
    assert "0.27.0" not in merged.json()["engine_refs"]
    assert "core-0" in merged.json()["engine_refs"]

    forbidden_versions = client.get("/v1/admin/bench/versions", headers=_bearer(other.json()["token"]))
    assert forbidden_versions.status_code == 403
    assert forbidden_versions.json()["detail"] == DETAIL_ADMIN
    forbidden_run = client.get(f"/v1/admin/bench/runs/{first['id']}", headers=_bearer(other.json()["token"]))
    assert forbidden_run.status_code == 403
    assert forbidden_run.json()["detail"] == DETAIL_ADMIN

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
    assert "model" in maximal.json() and "manual" in maximal.json()

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
