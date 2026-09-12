from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_admin, require_database
from doux_planning.api.db import BenchJob, BenchRun, session_scope
from doux_planning.api.generate import _cycle_recap_json, _cycle_score_json, _fact_json, _shift_json
from doux_planning.api.sandbox import parse_shift
from doux_planning.bench import (
    BENCH_CATEGORY_ORDER,
    BenchListing,
    BenchOutcome,
    UnknownBenchDataset,
    bench_dir,
    engine_ref,
    list_bench_datasets,
    load_bench_dataset,
    run_bench,
)
from doux_planning.context import cycle_recap_from_draft, expand_typical_week
from doux_planning.engine import PlanningDraft, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import SearchEffort, Team

SCOPES = ("all", "category", "dataset")
EXPORT_SCOPES = ("dataset", "below_manuel")
EFFORTS = ("minimal", "optimized", "maximal")
SYNC_EFFORTS = ("minimal", "optimized")
DETAIL_BENCH_MISSING = "Jeu introuvable."
DETAIL_BENCH_RUN_MISSING = "Aucun run pour ce jeu."
DETAIL_BENCH_JOB_MISSING = "Calcul introuvable."
DETAIL_BENCH_FAILED = "Le calcul a échoué."
LEGACY_ENGINE_REF = "0.27.0"
CANONICAL_CORE_ZERO = "core-0"


def bench_app_version() -> str:
    return engine_ref()


def _display_engine_ref(stored: str | None) -> str:
    if stored == LEGACY_ENGINE_REF:
        return CANONICAL_CORE_ZERO
    return stored or ""


def _run_summary(row: BenchRun) -> dict[str, Any]:
    ref = _display_engine_ref(row.app_version)
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "engine_ref": ref,
        "app_version": ref,
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
        app_version=outcome.engine_ref,
        category=outcome.category,
        dataset_id=outcome.id,
        search_effort=outcome.search_effort.value,
        duration_seconds=max(0.0, float(outcome.duration_seconds)),
        score=_cycle_score_json(outcome.score),
        expected_score=_cycle_score_json(outcome.expected_score),
        deltas=dict(outcome.deltas),
        assignments=[_shift_json(shift) for shift in outcome.assignments],
        warnings=[_fact_json(item) for item in outcome.facts],
    )
    with session_scope() as db:
        db.add(row)
        db.flush()
        run_id = row.id
    with session_scope() as db:
        stored = db.get(BenchRun, run_id)
        assert stored is not None
        return stored


def _active_bench_job(db, category: str, dataset_id: str, effort: str) -> BenchJob | None:
    return db.scalars(
        select(BenchJob).where(
            BenchJob.category == category,
            BenchJob.dataset_id == dataset_id,
            BenchJob.search_effort == effort,
            BenchJob.status.in_(("queued", "running")),
        )
    ).first()


def _enqueue_bench_job(category: str, dataset_id: str, effort: str) -> str:
    try:
        with session_scope() as db:
            existing = _active_bench_job(db, category, dataset_id, effort)
            if existing is not None:
                return existing.id
            job_id = secrets.token_urlsafe(12)
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
                    heartbeat_at=None,
                )
            )
            db.flush()
            return job_id
    except IntegrityError:
        with session_scope() as db:
            existing = _active_bench_job(db, category, dataset_id, effort)
            if existing is None:
                raise
            return existing.id


def _employee_slice(person) -> dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "role": {"name": person.role.name, "level": person.role.level, "team": person.role.team.value},
        "team": person.team.value,
    }


def _as_shifts(assignments) -> tuple:
    if not assignments:
        return ()
    first = next(iter(assignments))
    if isinstance(first, dict):
        return tuple(parse_shift(item) for item in assignments)
    return tuple(assignments)


def _salle_draft(dataset, assignments) -> PlanningDraft:
    state = dataset.state
    employees = tuple(person for person in state.employees if person.team == Team.SALLE)
    structures = tuple(item for item in expand_typical_week(state) if item.team == Team.SALLE)
    return PlanningDraft(
        employees=employees,
        structures=structures,
        hours=state.hours,
        legal_rules=default_legal_rules(),
        assignments=tuple(assignments),
    )


def _cycle_slice(dataset, assignments) -> dict[str, Any]:
    shifts = _as_shifts(assignments)
    draft = _salle_draft(dataset, shifts)
    result = evaluate(draft)
    recap = cycle_recap_from_draft(draft, result)
    body = {"assignments": [_shift_json(shift) for shift in result.assignments]}
    body.update(_cycle_recap_json(recap))
    return body


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
    ref = engine_ref()
    return {
        "engine_ref": ref,
        "app_version": ref,
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


def _compare_body(row: BenchRun) -> dict[str, Any]:
    try:
        dataset = load_bench_dataset(row.category, row.dataset_id)
    except UnknownBenchDataset as exc:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING) from exc
    body = _run_summary(row)
    body["employees"] = [_employee_slice(person) for person in dataset.state.employees]
    body["model"] = _cycle_slice(dataset, row.assignments)
    body["manual"] = _cycle_slice(dataset, dataset.expected)
    return body


def get_run(authorization: str | None, run_id: str) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        row = db.get(BenchRun, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
        return _compare_body(row)


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
    current = engine_ref()
    with session_scope() as db:
        rows = list(
            db.scalars(
                select(BenchRun)
                .where(
                    BenchRun.category == category,
                    BenchRun.dataset_id == dataset_id,
                    BenchRun.search_effort == search_effort,
                )
                .order_by(BenchRun.created_at.desc(), BenchRun.id.desc())
            )
        )
    row = next((item for item in rows if _display_engine_ref(item.app_version) == current), None)
    if row is None:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
    return _compare_body(row)


def _score_global(score: Any) -> float | None:
    if not isinstance(score, dict) or score.get("global") is None:
        return None
    return float(score["global"])


def _below_manuel(row: BenchRun) -> bool:
    model = _score_global(row.score)
    manual = _score_global(row.expected_score)
    if model is None or manual is None:
        return False
    return model < manual


def _runs_newest() -> list[BenchRun]:
    with session_scope() as db:
        return list(db.scalars(select(BenchRun).order_by(BenchRun.created_at.desc(), BenchRun.id.desc())))


def _latest_current_runs_map() -> dict[tuple[str, str], dict[str, BenchRun]]:
    current = engine_ref()
    grouped: dict[tuple[str, str], dict[str, BenchRun]] = {}
    for row in _runs_newest():
        if _display_engine_ref(row.app_version) != current:
            continue
        bucket = grouped.setdefault((row.category, row.dataset_id), {})
        if row.search_effort not in bucket:
            bucket[row.search_effort] = row
    return grouped


def _version_cell(row: BenchRun) -> dict[str, Any]:
    return {
        "run_id": row.id,
        "global": _score_global(row.score),
        "deltas": dict(row.deltas),
        "duration_seconds": row.duration_seconds,
    }


def list_versions(authorization: str | None) -> dict[str, Any]:
    require_admin(authorization)
    newest = _runs_newest()
    oldest = list(reversed(newest))
    engine_refs: list[str] = []
    for row in oldest:
        ref = _display_engine_ref(row.app_version)
        if ref and ref not in engine_refs:
            engine_refs.append(ref)
    latest: dict[tuple[str, str, str, str], BenchRun] = {}
    first_run: dict[tuple[str, str], BenchRun] = {}
    for row in newest:
        key = (row.category, row.dataset_id, _display_engine_ref(row.app_version), row.search_effort)
        latest.setdefault(key, row)
    for row in oldest:
        first_run.setdefault((row.category, row.dataset_id), row)
    datasets: list[dict[str, Any]] = []
    for item in list_bench_datasets():
        first = first_run.get((item.category, item.id))
        by_ref: dict[str, dict[str, Any]] = {}
        for ref in engine_refs:
            by_ref[ref] = {
                effort: (
                    _version_cell(latest[(item.category, item.id, ref, effort)])
                    if (item.category, item.id, ref, effort) in latest
                    else None
                )
                for effort in EFFORTS
            }
        datasets.append(
            {
                "category": item.category,
                "id": item.id,
                "name": item.name,
                "challenge_fr": item.challenge_fr,
                "manual": None if first is None else {"global": _score_global(first.expected_score)},
                "by_ref": by_ref,
            }
        )
    return {"engine_ref": engine_ref(), "engine_refs": engine_refs, "datasets": datasets}


def _context_json(category: str, dataset_id: str) -> dict[str, Any]:
    path = bench_dir() / category / dataset_id / "context.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        employees = raw.get("employees")
        if isinstance(employees, list):
            cleaned = []
            for person in employees:
                if isinstance(person, dict):
                    item = dict(person)
                    item.pop("invite_token", None)
                    cleaned.append(item)
                else:
                    cleaned.append(person)
            raw = dict(raw)
            raw["employees"] = cleaned
    return raw


def _dataset_pack_entry(listing: BenchListing, latest: dict[str, BenchRun]) -> dict[str, Any]:
    dataset = load_bench_dataset(listing.category, listing.id)
    efforts: list[dict[str, Any]] = []
    for effort in EFFORTS:
        row = latest.get(effort)
        if row is None:
            continue
        efforts.append(
            {
                "search_effort": effort,
                "run_id": row.id,
                "engine_ref": _display_engine_ref(row.app_version),
                "duration_seconds": row.duration_seconds,
                "below_manuel": _below_manuel(row),
                "model": _cycle_slice(dataset, row.assignments),
                "deltas": dict(row.deltas),
            }
        )
    return {
        "category": listing.category,
        "id": listing.id,
        "name": listing.name,
        "challenge_fr": listing.challenge_fr,
        "context": _context_json(listing.category, listing.id),
        "manual": _cycle_slice(dataset, dataset.expected),
        "efforts": efforts,
    }


def export_pack(
    authorization: str | None,
    *,
    scope: str | None,
    category: str | None = None,
    dataset_id: str | None = None,
) -> dict[str, Any]:
    require_admin(authorization)
    require_database()
    if scope not in EXPORT_SCOPES:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    listed = {(item.category, item.id): item for item in list_bench_datasets()}
    grouped = _latest_current_runs_map()
    datasets: list[dict[str, Any]] = []
    if scope == "dataset":
        if not isinstance(category, str) or not category or not isinstance(dataset_id, str) or not dataset_id:
            raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
        listing = listed.get((category, dataset_id))
        if listing is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
        latest = grouped.get((category, dataset_id)) or {}
        if not latest:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
        datasets.append(_dataset_pack_entry(listing, latest))
    else:
        for item in list_bench_datasets():
            latest = grouped.get((item.category, item.id)) or {}
            if not latest:
                continue
            if not any(_below_manuel(row) for row in latest.values()):
                continue
            datasets.append(_dataset_pack_entry(item, latest))
    ref = engine_ref()
    return {
        "export_version": 1,
        "kind": "bench-pack",
        "engine_ref": ref,
        "app_version": ref,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "datasets": datasets,
    }


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
