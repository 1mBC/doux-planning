from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_admin, require_database
from doux_planning.api.db import BenchJob, BenchRun, session_scope
from doux_planning.api.generate import _cycle_score_json, _fact_json, _shift_json
from doux_planning.bench import (
    BENCH_CATEGORY_ORDER,
    BenchOutcome,
    UnknownBenchDataset,
    bench_dir,
    list_bench_datasets,
    load_bench_dataset,
    run_bench,
)
from doux_planning.types import SearchEffort

SCOPES = ("all", "category", "dataset")
EFFORTS = ("minimal", "optimized", "maximal")
SYNC_EFFORTS = ("minimal", "optimized")
DETAIL_BENCH_MISSING = "Jeu introuvable."
DETAIL_BENCH_RUN_MISSING = "Aucun run pour ce jeu."
DETAIL_BENCH_JOB_MISSING = "Calcul introuvable."
DETAIL_BENCH_FAILED = "Le calcul a échoué."


def bench_app_version() -> str:
    return (bench_dir() / "VERSION").read_text(encoding="utf-8").strip()


def _run_summary(row: BenchRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "app_version": row.app_version,
        "category": row.category,
        "dataset_id": row.dataset_id,
        "search_effort": row.search_effort,
        "duration_seconds": row.duration_seconds,
        "score": dict(row.score),
        "expected_score": dict(row.expected_score),
        "deltas": dict(row.deltas),
    }


def persist_bench_outcome(outcome: BenchOutcome) -> BenchRun:
    created_at = datetime.now(timezone.utc)
    row = BenchRun(
        id=secrets.token_urlsafe(12),
        created_at=created_at,
        app_version=bench_app_version(),
        category=outcome.category,
        dataset_id=outcome.id,
        search_effort=outcome.search_effort.value,
        duration_seconds=max(0.0, float(outcome.duration_seconds)),
        score=_cycle_score_json(outcome.score),
        expected_score=_cycle_score_json(outcome.expected_score),
        deltas=dict(outcome.deltas),
        assignments=[_shift_json(shift) for shift in outcome.assignments],
        warnings=[_fact_json(warning) for warning in outcome.warnings],
    )
    with session_scope() as db:
        db.add(row)
        db.flush()
        run_id = row.id
    with session_scope() as db:
        stored = db.get(BenchRun, run_id)
        assert stored is not None
        return stored


def _enqueue_bench_job(category: str, dataset_id: str, effort: str) -> str:
    job_id = secrets.token_urlsafe(12)
    with session_scope() as db:
        db.add(
            BenchJob(
                id=job_id,
                category=category,
                dataset_id=dataset_id,
                search_effort=effort,
                status="queued",
                error=None,
                run_id=None,
                created_at=datetime.now(timezone.utc),
            )
        )
    return job_id


def _known_targets() -> list[tuple[str, str]]:
    return [(item.category, item.id) for item in list_bench_datasets()]


def _parse_run_body(body: dict[str, Any]) -> tuple[str, str, list[tuple[str, str]]]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    scope = body.get("scope")
    effort = body.get("search_effort")
    category = body.get("category")
    dataset_id = body.get("dataset_id")
    if scope not in SCOPES or effort not in EFFORTS:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    known = _known_targets()
    if scope == "all":
        return scope, effort, known
    if not isinstance(category, str) or not category:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if category not in BENCH_CATEGORY_ORDER:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if scope == "category":
        return scope, effort, [item for item in known if item[0] == category]
    if not isinstance(dataset_id, str) or not dataset_id:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if (category, dataset_id) not in known:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
    return scope, effort, [(category, dataset_id)]


def list_datasets(authorization: str | None) -> dict[str, Any]:
    require_admin(authorization)
    return {
        "app_version": bench_app_version(),
        "datasets": [
            {
                "category": item.category,
                "id": item.id,
                "name": item.name,
                "challenge_fr": item.challenge_fr,
            }
            for item in list_bench_datasets()
        ],
    }


def list_runs(
    authorization: str | None,
    *,
    category: str | None = None,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        query = select(BenchRun)
        if category:
            query = query.where(BenchRun.category == category)
        if dataset_id:
            query = query.where(BenchRun.dataset_id == dataset_id)
        rows = db.scalars(query.order_by(BenchRun.created_at.desc(), BenchRun.id.desc())).all()
        return {"runs": [_run_summary(row) for row in rows]}


def get_run(authorization: str | None, run_id: str) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        row = db.get(BenchRun, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
        body = _run_summary(row)
        body["assignments"] = list(row.assignments or [])
        body["facts"] = list(row.warnings or [])
        return body


def get_job(authorization: str | None, job_id: str) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        job = db.get(BenchJob, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_JOB_MISSING)
        body: dict[str, Any] = {
            "job_id": job.id,
            "category": job.category,
            "dataset_id": job.dataset_id,
            "search_effort": job.search_effort,
            "status": job.status,
        }
        if job.status == "failed" and job.error:
            body["error"] = job.error
        if job.status == "done" and job.run_id:
            body["run_id"] = job.run_id
        return body


def compare(authorization: str | None, category: str, dataset_id: str, search_effort: str) -> dict[str, Any]:
    require_admin(authorization)
    if search_effort not in EFFORTS:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    with session_scope() as db:
        row = db.scalars(
            select(BenchRun)
            .where(
                BenchRun.category == category,
                BenchRun.dataset_id == dataset_id,
                BenchRun.search_effort == search_effort,
            )
            .order_by(BenchRun.created_at.desc(), BenchRun.id.desc())
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
        try:
            dataset = load_bench_dataset(category, dataset_id)
        except UnknownBenchDataset as exc:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING) from exc
        body = _run_summary(row)
        body["assignments"] = list(row.assignments or [])
        body["facts"] = list(row.warnings or [])
        body["expected"] = {
            "assignments": [_shift_json(shift) for shift in dataset.expected],
            "score": dict(row.expected_score),
        }
        body["expected_score"] = dict(row.expected_score)
        return body


def post_run(authorization: str | None, body: dict[str, Any]) -> dict[str, Any] | JSONResponse:
    require_admin(authorization)
    require_database()
    scope, effort, targets = _parse_run_body(body)
    async_run = scope in ("all", "category") or effort == "maximal"
    if async_run:
        job_ids = [_enqueue_bench_job(category, dataset_id, effort) for category, dataset_id in targets]
        return JSONResponse(status_code=202, content={"job_ids": job_ids, "status": "queued"})
    category, dataset_id = targets[0]
    try:
        outcome = run_bench(category, dataset_id, SearchEffort(effort))
    except UnknownBenchDataset as exc:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING) from exc
    row = persist_bench_outcome(outcome)
    return {"runs": [_run_summary(row)]}
