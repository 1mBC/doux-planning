from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, DETAIL_DB, DETAIL_SESSION, promote_admin_email
from doux_planning.api.bench import DETAIL_ENGINE_REF_UNKNOWN, DETAIL_UNKNOWN_ENGINE
from doux_planning.api.db import BenchEngine, BenchJob, BenchRun, LiveEngine, get_engine, reset_engine, session_scope
from doux_planning.api.generate import get_effective_bench_engine_ref, get_effective_engine_ref
from doux_planning.bench import BenchListing, bench_dir
from doux_planning.engines.registry import list_engine_refs

DETAIL_UNKNOWN_BENCH = "Moteur inconnu."


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_engine_choice_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def _alembic_config():
    from alembic.config import Config

    return Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))


def _columns(table: str) -> list[tuple[str, str, bool]]:
    insp = inspect(get_engine())
    return [(col["name"], str(col["type"]), bool(col["nullable"])) for col in insp.get_columns(table)]


def _set_row(model, value: str | None, *, present: bool) -> None:
    with session_scope() as db:
        row = db.get(model, 1)
        if not present:
            if row is not None:
                db.delete(row)
            return
        if row is None:
            db.add(model(id=1, engine_ref=value))
        else:
            row.engine_ref = value


def _row_ref(model) -> str | None:
    with session_scope() as db:
        row = db.get(model, 1)
        if row is None:
            return None
        return row.engine_ref


def _admin(monkeypatch) -> tuple[TestClient, dict[str, str]]:
    client = _client()
    email = f"bench-engine-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": "password1"},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    monkeypatch.setenv("ADMIN_EMAIL", email)
    promote_admin_email()
    headers = _bearer(token)
    assert client.get("/v1/me", headers=headers).json()["admin"] is True
    return client, headers


def _insert_run(*, app_version: str, category: str, dataset_id: str, search_effort: str, score_global: float, expected_global: float) -> str:
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


def _fail_jobs(job_ids: list[str]) -> None:
    with session_scope() as db:
        for job_id in job_ids:
            job = db.get(BenchJob, job_id)
            if job is not None and job.status in ("queued", "running"):
                job.status = "failed"
                job.error = "test cleanup"


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_bench_engine_table_upgrade_and_downgrade():
    from alembic import command

    reset_engine()
    names = inspect(get_engine()).get_table_names()
    assert "bench_engine" in names
    assert "live_engine" in names
    columns = {name: (type_name, nullable) for name, type_name, nullable in _columns("bench_engine")}
    assert columns["id"][1] is False
    assert "INT" in columns["id"][0].upper()
    assert columns["engine_ref"] == ("VARCHAR", True) or columns["engine_ref"][1] is True
    assert columns["engine_ref"][1] is True
    pk = inspect(get_engine()).get_pk_constraint("bench_engine")["constrained_columns"]
    assert pk == ["id"]
    live_before = _columns("live_engine")

    cfg = _alembic_config()
    reset_engine()
    try:
        command.downgrade(cfg, "20260922_0019")
        reset_engine()
        after_down = inspect(get_engine()).get_table_names()
        assert "bench_engine" not in after_down
        assert "live_engine" in after_down
    finally:
        command.upgrade(cfg, "head")
        reset_engine()
    assert "bench_engine" in inspect(get_engine()).get_table_names()
    assert _columns("live_engine") == live_before


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_bench_and_live_resolvers_rewrite_missing_blank_and_unknown(monkeypatch):
    from pathlib import Path as FsPath

    fallback = list_engine_refs()[-1]
    assert not (bench_dir() / "VERSION").is_file()
    original = FsPath.read_text

    def guarded(self, *args, **kwargs):
        if self.name == "VERSION":
            raise AssertionError(f"read {self}")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(FsPath, "read_text", guarded)
    resolvers = (
        (BenchEngine, get_effective_bench_engine_ref),
        (LiveEngine, get_effective_engine_ref),
    )
    for model, resolve in resolvers:
        _set_row(model, None, present=False)
        assert resolve() == fallback
        assert _row_ref(model) == fallback
        assert resolve() == fallback

        _set_row(model, "", present=True)
        assert resolve() == fallback
        assert _row_ref(model) == fallback
        assert resolve() == fallback

        _set_row(model, None, present=True)
        assert resolve() == fallback
        assert _row_ref(model) == fallback
        assert resolve() == fallback

        _set_row(model, "hors-liste", present=True)
        assert resolve() == fallback
        assert _row_ref(model) == fallback
        assert resolve() == fallback

        _set_row(model, "core-2", present=True)
        assert resolve() == "core-2"
        assert _row_ref(model) == "core-2"
        assert resolve() == "core-2"


def test_put_bench_engine_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    response = client.put(
        "/v1/admin/bench/engine",
        headers=_bearer("x"),
        json={"engine_ref": "core-2"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == DETAIL_DB


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_put_bench_engine_admin_only_and_rejects_unknown(monkeypatch):
    client, headers = _admin(monkeypatch)
    registre = list(list_engine_refs())
    _set_row(BenchEngine, None, present=False)
    _insert_run(
        app_version="legacy-extra",
        category="tight",
        dataset_id="halles",
        search_effort="optimized",
        score_global=1.0,
        expected_global=8.0,
    )

    missing = client.put("/v1/admin/bench/engine", json={"engine_ref": "core-2"})
    assert missing.status_code == 401
    assert missing.json()["detail"] == DETAIL_SESSION

    other = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"user-{secrets.token_hex(4)}@example.com", "password": "password1"},
    )
    assert other.status_code == 201
    forbidden = client.put(
        "/v1/admin/bench/engine",
        headers=_bearer(other.json()["token"]),
        json={"engine_ref": "core-2"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == DETAIL_ADMIN
    assert _row_ref(BenchEngine) is None

    for body in (
        {"engine_ref": "inconnu"},
        {"engine_ref": ""},
        {"engine_ref": 123},
        {"engine_ref": None},
        {},
    ):
        rejected = client.put("/v1/admin/bench/engine", headers=headers, json=body)
        assert rejected.status_code == 400
        assert rejected.json()["detail"] == DETAIL_UNKNOWN_BENCH
        assert _row_ref(BenchEngine) is None

    saved = client.put("/v1/admin/bench/engine", headers=headers, json={"engine_ref": "core-2"})
    assert saved.status_code == 200
    assert saved.json()["engine_ref"] == "core-2"
    assert saved.json()["engine_refs"] == registre
    assert "legacy-extra" not in saved.json()["engine_refs"]
    assert _row_ref(BenchEngine) == "core-2"

    for body in ({"engine_ref": "inconnu"}, {"engine_ref": ""}, {"engine_ref": 123}):
        rejected = client.put("/v1/admin/bench/engine", headers=headers, json=body)
        assert rejected.status_code == 400
        assert rejected.json()["detail"] == DETAIL_UNKNOWN_ENGINE
        assert _row_ref(BenchEngine) == "core-2"

    versions = client.get("/v1/admin/bench/versions", headers=headers)
    assert versions.status_code == 200
    assert versions.json()["engine_ref"] == "core-2"
    assert versions.json()["engine_refs"][: len(registre)] == registre
    assert "legacy-extra" in versions.json()["engine_refs"]
    assert versions.json()["engine_refs"].index("legacy-extra") >= len(registre)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_bench_run_uses_resolver_or_explicit_engine(monkeypatch):
    client, headers = _admin(monkeypatch)
    fallback = list_engine_refs()[-1]
    created: list[str] = []

    def post(body: dict) -> object:
        return client.post("/v1/admin/bench/run", headers=headers, json=body)

    def one_job(response) -> str:
        assert response.status_code == 202
        job_ids = response.json()["job_ids"]
        assert job_ids
        created.extend(job_ids)
        return job_ids[0]

    try:
        _set_row(BenchEngine, None, present=False)
        omitted = post(
            {"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "maximal"}
        )
        with session_scope() as db:
            job = db.get(BenchJob, one_job(omitted))
            assert job is not None
            assert job.engine_ref == fallback
        assert _row_ref(BenchEngine) == fallback

        _set_row(BenchEngine, "core-4", present=True)
        empty = post(
            {
                "scope": "dataset",
                "category": "tight",
                "dataset_id": "halles",
                "search_effort": "maximal",
                "engine_ref": "",
            }
        )
        with session_scope() as db:
            job = db.get(BenchJob, one_job(empty))
            assert job is not None
            assert job.engine_ref == "core-4"
        assert _row_ref(BenchEngine) == "core-4"

        explicit = post(
            {
                "scope": "dataset",
                "category": "tight",
                "dataset_id": "halles",
                "search_effort": "maximal",
                "engine_ref": "core-2",
            }
        )
        with session_scope() as db:
            job = db.get(BenchJob, one_job(explicit))
            assert job is not None
            assert job.engine_ref == "core-2"
        assert _row_ref(BenchEngine) == "core-4"

        invalid = post(
            {
                "scope": "dataset",
                "category": "tight",
                "dataset_id": "halles",
                "search_effort": "maximal",
                "engine_ref": "inconnu",
            }
        )
        assert invalid.status_code == 400
        assert invalid.json()["detail"] == DETAIL_ENGINE_REF_UNKNOWN
        assert _row_ref(BenchEngine) == "core-4"

        monkeypatch.setattr(
            "doux_planning.api.bench.list_bench_datasets",
            lambda: [BenchListing(category="tight", id="engine-choice-gap", name="Gap", challenge_fr="gap")],
        )
        gaps = post({"scope": "gaps", "origin": "catalogue", "engine_ref": "nope"})
        assert gaps.status_code == 202
        gap_ids = gaps.json()["job_ids"]
        created.extend(gap_ids)
        with session_scope() as db:
            jobs = [db.get(BenchJob, job_id) for job_id in gap_ids]
        refs = {job.engine_ref for job in jobs if job is not None and job.dataset_id == "engine-choice-gap"}
        assert refs == set(list_engine_refs())
        assert len([job for job in jobs if job is not None and job.dataset_id == "engine-choice-gap"]) == 3 * len(
            list_engine_refs()
        )
        assert _row_ref(BenchEngine) == "core-4"
    finally:
        _fail_jobs(created)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_compare_and_below_manuel_follow_stored_bench_engine(monkeypatch):
    client, headers = _admin(monkeypatch)
    _set_row(BenchEngine, "core-2", present=True)
    core2_id = _insert_run(
        app_version="core-2",
        category="tight",
        dataset_id="halles",
        search_effort="minimal",
        score_global=1.0,
        expected_global=8.0,
    )
    mix_halles = _insert_run(
        app_version="mix-0",
        category="tight",
        dataset_id="halles",
        search_effort="minimal",
        score_global=1.0,
        expected_global=8.0,
    )
    mix_nocturne = _insert_run(
        app_version="mix-0",
        category="clock",
        dataset_id="nocturne",
        search_effort="minimal",
        score_global=1.0,
        expected_global=8.0,
    )

    compared = client.get("/v1/admin/bench/compare/tight/halles/minimal", headers=headers)
    assert compared.status_code == 200
    assert compared.json()["id"] == core2_id
    assert compared.json()["engine_ref"] == "core-2"

    below = client.get("/v1/admin/bench/export", headers=headers, params={"scope": "below_manuel"})
    assert below.status_code == 200
    assert below.json()["engine_ref"] == below.json()["app_version"] == "core-2"
    efforts = [effort for item in below.json()["datasets"] for effort in item["efforts"]]
    assert all(item["engine_ref"] == "core-2" for item in efforts)
    assert core2_id in {item["run_id"] for item in efforts}
    assert mix_halles not in {item["run_id"] for item in efforts}
    assert mix_nocturne not in {item["run_id"] for item in efforts}

    dataset = client.get(
        "/v1/admin/bench/export",
        headers=headers,
        params={"scope": "dataset", "category": "tight", "dataset_id": "halles"},
    )
    assert dataset.status_code == 200
    dataset_efforts = dataset.json()["datasets"][0]["efforts"]
    dataset_refs = {item["engine_ref"] for item in dataset_efforts}
    assert "core-2" in dataset_refs
    assert "mix-0" in dataset_refs
    assert {core2_id, mix_halles} <= {item["run_id"] for item in dataset_efforts}

    bank = client.get("/v1/admin/bench/export", headers=headers, params={"scope": "bank"})
    assert bank.status_code == 200
    halles = next(item for item in bank.json()["datasets"] if item["category"] == "tight" and item["id"] == "halles")
    bank_refs = {item["engine_ref"] for item in halles["efforts"]}
    assert "core-2" in bank_refs
    assert "mix-0" in bank_refs


def test_detail_constants_match_the_contract():
    assert DETAIL_UNKNOWN_ENGINE == "Moteur inconnu."
    assert DETAIL_UNKNOWN_BENCH == "Moteur inconnu."
    assert DETAIL_ENGINE_REF_UNKNOWN == "engine_ref inconnu"
