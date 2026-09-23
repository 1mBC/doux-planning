from __future__ import annotations

import json
import secrets
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import defer

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_admin, require_database
from doux_planning.api.bench_import import (
    DETAIL_NO_SALLE,
    IMPORTED_CATEGORY,
    context_has_salle,
    get_imported_row,
    imported_context,
    imported_override,
    list_imported_rows,
    load_imported_dataset,
)
from doux_planning.api.db import (
    BenchEngine,
    BenchImportedDataset,
    BenchJob,
    BenchRun,
    BenchTombstone,
    session_scope,
)
from doux_planning.api.generate import (
    BENCH_ENGINE_ROW_ID,
    DETAIL_UNKNOWN_ENGINE,
    _cycle_recap_json,
    _cycle_score_json,
    _fact_json,
    _shift_json,
    get_effective_bench_engine_ref,
)
from doux_planning.api.sandbox import parse_shift
from doux_planning.bench import (
    BENCH_CATEGORY_ORDER,
    BenchListing,
    BenchOutcome,
    UnknownBenchDataset,
    bench_dir,
    list_bench_datasets,
    list_engine_refs,
    load_bench_dataset,
    run_bench_on,
)
from doux_planning.context import cycle_recap_from_draft, expand_typical_week
from doux_planning.engine import SEARCH_SECONDS, PlanningDraft, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import SearchEffort, Team

SCOPES = ("all", "category", "dataset")
EXPORT_SCOPES = ("dataset", "below_manuel", "bank")
EFFORTS = ("minimal", "optimized", "maximal")
SYNC_EFFORTS = ("minimal", "optimized")
TRACE_KEYS = (
    "seeder",
    "seed_index",
    "n_locks",
    "calendars_by_seeder",
    "calendars_total",
    "seeds_infeasible",
    "attempt_key",
)
DETAIL_BENCH_MISSING = "Jeu introuvable."
DETAIL_BENCH_RUN_MISSING = "Aucun run pour ce jeu."
DETAIL_BENCH_JOB_MISSING = "Calcul introuvable."
DETAIL_BENCH_BATCH_MISSING = "Calcul introuvable."
DETAIL_BENCH_FAILED = "Le calcul a échoué."
DETAIL_ENGINE_REF_UNKNOWN = "engine_ref inconnu"
LEGACY_ENGINE_REF = "0.27.0"
CANONICAL_CORE_ZERO = "core-0"


def bench_app_version() -> str:
    return get_effective_bench_engine_ref()


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
    expected_score = _cycle_score_json(outcome.expected_score)
    deltas = dict(outcome.deltas)
    override = imported_override(outcome.id)
    if override is not None:
        expected_score = dict(expected_score)
        expected_score["global"] = override
        model_global = outcome.score.global_score
        deltas = dict(deltas)
        deltas["global"] = None if model_global is None else float(model_global) - float(override)
    row = BenchRun(
        id=secrets.token_urlsafe(12),
        created_at=created_at,
        app_version=outcome.engine_ref,
        category=outcome.category,
        dataset_id=outcome.id,
        search_effort=outcome.search_effort.value,
        duration_seconds=max(0.0, float(outcome.duration_seconds)),
        score=_cycle_score_json(outcome.score),
        expected_score=expected_score,
        deltas=deltas,
        assignments=[_shift_json(shift) for shift in outcome.assignments],
        warnings=[_fact_json(item) for item in outcome.facts],
        trace=asdict(outcome.trace) if outcome.trace is not None else None,
    )
    with session_scope() as db:
        db.add(row)
        db.flush()
        run_id = row.id
    with session_scope() as db:
        stored = db.get(BenchRun, run_id)
        assert stored is not None
        return stored


def _trace_json(row: BenchRun) -> dict[str, Any] | None:
    trace = row.trace
    if not isinstance(trace, dict):
        return None
    return dict(trace)


def _trace_complete(trace: Any) -> bool:
    return isinstance(trace, dict) and all(key in trace for key in TRACE_KEYS)


def _active_bench_job(db, category: str, dataset_id: str, effort: str, engine_ref_value: str) -> BenchJob | None:
    return db.scalars(
        select(BenchJob).where(
            BenchJob.category == category,
            BenchJob.dataset_id == dataset_id,
            BenchJob.search_effort == effort,
            BenchJob.engine_ref == engine_ref_value,
            BenchJob.status.in_(("queued", "running")),
        )
    ).first()


def _enqueue_bench_job(
    category: str,
    dataset_id: str,
    effort: str,
    engine_ref_value: str,
    batch_id: str,
) -> str:
    try:
        with session_scope() as db:
            existing = _active_bench_job(db, category, dataset_id, effort, engine_ref_value)
            if existing is not None:
                existing.batch_id = batch_id
                db.flush()
                return existing.id
            job_id = secrets.token_urlsafe(12)
            db.add(
                BenchJob(
                    id=job_id,
                    category=category,
                    dataset_id=dataset_id,
                    search_effort=effort,
                    engine_ref=engine_ref_value,
                    status="queued",
                    error=None,
                    run_id=None,
                    batch_id=batch_id,
                    created_at=datetime.now(timezone.utc),
                    heartbeat_at=None,
                    started_at=None,
                )
            )
            db.flush()
            return job_id
    except IntegrityError:
        with session_scope() as db:
            existing = _active_bench_job(db, category, dataset_id, effort, engine_ref_value)
            if existing is None:
                raise
            existing.batch_id = batch_id
            db.flush()
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


def resolve_bench_dataset(category: str, dataset_id: str):
    folder = bench_dir() / category / dataset_id
    if (folder / "context.json").is_file() and (folder / "expected.json").is_file():
        return load_bench_dataset(category, dataset_id)
    return load_imported_dataset(category, dataset_id)


def _catalogue_on_disk(category: str, dataset_id: str) -> bool:
    folder = bench_dir() / category / dataset_id
    return (folder / "context.json").is_file() and (folder / "expected.json").is_file()


def _tombstone_keys() -> set[tuple[str, str]]:
    require_database()
    with session_scope() as db:
        rows = db.execute(select(BenchTombstone.category, BenchTombstone.dataset_id)).all()
        return {(category, dataset_id) for category, dataset_id in rows}


def _imported_listings() -> list[BenchListing]:
    return [
        BenchListing(category=row.category, id=row.id, name=row.name, challenge_fr=row.challenge_fr)
        for row in list_imported_rows(include_context=False)
    ]


def _parse_origin(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    if raw in ("catalogue", "imported"):
        return raw
    raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)


def _listing_origin(item: BenchListing) -> str:
    return "imported" if item.category == IMPORTED_CATEGORY else "catalogue"


def _all_listings(origin: str | None = None) -> list[BenchListing]:
    hidden = _tombstone_keys()
    items: list[BenchListing] = []
    if origin != "imported":
        items.extend(list_bench_datasets())
    if origin != "catalogue":
        items.extend(_imported_listings())
    return [item for item in items if (item.category, item.id) not in hidden]


def _known_targets(origin: str | None = None) -> list[tuple[str, str]]:
    return [(item.category, item.id) for item in _all_listings(origin)]


def _target_has_salle(category: str, dataset_id: str) -> bool:
    if category != IMPORTED_CATEGORY:
        return True
    row = get_imported_row(dataset_id)
    if row is None:
        return False
    return context_has_salle(row.context if isinstance(row.context, dict) else None)


def _parse_run_body(body: dict[str, Any]) -> tuple[str, str, list[tuple[str, str]], str]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    scope = body.get("scope")
    effort = body.get("search_effort")
    category = body.get("category")
    dataset_id = body.get("dataset_id")
    requested_ref = body.get("engine_ref")
    if scope not in SCOPES or effort not in EFFORTS:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if requested_ref is not None and requested_ref != "":
        if not isinstance(requested_ref, str) or requested_ref not in list_engine_refs():
            raise HTTPException(status_code=400, detail=DETAIL_ENGINE_REF_UNKNOWN)
        ref_to_use = requested_ref
    else:
        ref_to_use = get_effective_bench_engine_ref()
    origin = _parse_origin(body.get("origin"))
    known = _known_targets() if scope == "dataset" else _known_targets(origin)
    if scope == "all":
        return scope, effort, [item for item in known if _target_has_salle(*item)], ref_to_use
    if not isinstance(category, str) or not category:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if category not in BENCH_CATEGORY_ORDER and category != IMPORTED_CATEGORY:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if scope == "category":
        return scope, effort, [item for item in known if item[0] == category and _target_has_salle(*item)], ref_to_use
    if not isinstance(dataset_id, str) or not dataset_id:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if (category, dataset_id) not in known:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
    if not _target_has_salle(category, dataset_id):
        raise HTTPException(status_code=400, detail=DETAIL_NO_SALLE)
    return scope, effort, [(category, dataset_id)], ref_to_use


def list_datasets(authorization: str | None) -> dict[str, Any]:
    require_admin(authorization)
    hidden = _tombstone_keys()
    ref = get_effective_bench_engine_ref()
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
            if (item.category, item.id) not in hidden
        ],
    }


def put_bench_engine(authorization: str | None, body: dict[str, Any]) -> dict[str, Any]:
    require_admin(authorization)
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail=DETAIL_UNKNOWN_ENGINE)
    new_ref = body.get("engine_ref")
    if not isinstance(new_ref, str) or not new_ref or new_ref not in list_engine_refs():
        raise HTTPException(status_code=400, detail=DETAIL_UNKNOWN_ENGINE)
    with session_scope() as db:
        row = db.get(BenchEngine, BENCH_ENGINE_ROW_ID)
        if row is None:
            db.add(BenchEngine(id=BENCH_ENGINE_ROW_ID, engine_ref=new_ref))
        else:
            row.engine_ref = new_ref
    return {"engine_ref": new_ref, "engine_refs": list(list_engine_refs())}


def _purge_bench_results(db, category: str, dataset_id: str) -> None:
    db.execute(delete(BenchRun).where(BenchRun.category == category, BenchRun.dataset_id == dataset_id))
    db.execute(delete(BenchJob).where(BenchJob.category == category, BenchJob.dataset_id == dataset_id))


def delete_dataset(authorization: str | None, category: str, dataset_id: str) -> Response:
    require_admin(authorization)
    require_database()
    with session_scope() as db:
        imported_row = None
        if category == IMPORTED_CATEGORY:
            imported_row = db.get(BenchImportedDataset, dataset_id)
        tombstone = db.get(BenchTombstone, (category, dataset_id))
        on_disk = _catalogue_on_disk(category, dataset_id)
        if imported_row is None and tombstone is None and not on_disk:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
        if imported_row is not None:
            db.delete(imported_row)
        elif tombstone is None:
            db.add(
                BenchTombstone(
                    category=category,
                    dataset_id=dataset_id,
                    created_at=datetime.now(timezone.utc),
                )
            )
        _purge_bench_results(db, category, dataset_id)
    return Response(status_code=204)


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
        dataset = resolve_bench_dataset(row.category, row.dataset_id)
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
        return _compare_body(row) | {"trace": _trace_json(row)}


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
    current = get_effective_bench_engine_ref()
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


def _runs_newest(*, origin: str | None = None, cells_only: bool = False) -> list[BenchRun]:
    stmt = select(BenchRun).order_by(BenchRun.created_at.desc(), BenchRun.id.desc())
    if origin == "imported":
        stmt = stmt.where(BenchRun.category == IMPORTED_CATEGORY)
    elif origin == "catalogue":
        stmt = stmt.where(BenchRun.category != IMPORTED_CATEGORY)
    if cells_only:
        stmt = stmt.options(defer(BenchRun.assignments), defer(BenchRun.warnings), defer(BenchRun.trace))
    with session_scope() as db:
        return list(db.scalars(stmt))


def _latest_current_runs_map() -> dict[tuple[str, str], dict[str, BenchRun]]:
    current = get_effective_bench_engine_ref()
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


def list_versions(authorization: str | None, origin: str | None = None) -> dict[str, Any]:
    require_admin(authorization)
    origin_filter = _parse_origin(origin)
    newest = _runs_newest(origin=origin_filter, cells_only=True)
    oldest = list(reversed(newest))
    registre = list(list_engine_refs())
    extras: list[str] = []
    seen = set(registre)
    for row in oldest:
        ref = _display_engine_ref(row.app_version)
        if ref and ref not in seen:
            extras.append(ref)
            seen.add(ref)
    engine_refs = registre + extras
    latest: dict[tuple[str, str, str, str], BenchRun] = {}
    first_run: dict[tuple[str, str], BenchRun] = {}
    for row in newest:
        key = (row.category, row.dataset_id, _display_engine_ref(row.app_version), row.search_effort)
        latest.setdefault(key, row)
    for row in oldest:
        first_run.setdefault((row.category, row.dataset_id), row)
    datasets: list[dict[str, Any]] = []
    imported_rows = (
        {row.id: row for row in list_imported_rows(include_context=False)}
        if origin_filter != "catalogue"
        else {}
    )
    for item in _all_listings(origin_filter):
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
        listing_origin = _listing_origin(item)
        comment = None
        manual: dict[str, Any] | None
        if listing_origin == "imported":
            imported = imported_rows.get(item.id)
            comment = None if imported is None else imported.comment
            override = None if imported is None else imported.manual_score_override
            expected = {} if imported is None or not isinstance(imported.expected, dict) else imported.expected
            expected_assignments = expected.get("assignments") or []
            if override is not None:
                manual = {"global": override}
            elif expected_assignments:
                manual = None if first is None else {"global": _score_global(first.expected_score)}
            else:
                manual = None
        else:
            manual = None if first is None else {"global": _score_global(first.expected_score)}
        datasets.append(
            {
                "category": item.category,
                "id": item.id,
                "name": item.name,
                "challenge_fr": item.challenge_fr,
                "origin": listing_origin,
                "comment": comment,
                "manual": manual,
                "by_ref": by_ref,
            }
        )
    return {"engine_ref": get_effective_bench_engine_ref(), "engine_refs": engine_refs, "datasets": datasets}


def _strip_invite_tokens(raw: dict[str, Any]) -> dict[str, Any]:
    employees = raw.get("employees")
    if not isinstance(employees, list):
        return raw
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


def _context_json(category: str, dataset_id: str) -> dict[str, Any]:
    if category == IMPORTED_CATEGORY:
        stored = imported_context(dataset_id)
        if stored is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
        return _strip_invite_tokens(stored)
    path = bench_dir() / category / dataset_id / "context.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return _strip_invite_tokens(raw)
    return raw


def _dataset_pack_entry(listing: BenchListing, latest: dict[str, BenchRun]) -> dict[str, Any]:
    dataset = resolve_bench_dataset(listing.category, listing.id)
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
                "trace": _trace_json(row),
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


def _latest_runs_by_quad() -> dict[tuple[str, str, str, str], BenchRun]:
    latest: dict[tuple[str, str, str, str], BenchRun] = {}
    for row in _runs_newest():
        key = (
            row.category,
            row.dataset_id,
            _display_engine_ref(row.app_version),
            row.search_effort,
        )
        latest.setdefault(key, row)
    return latest


def _engine_refs_for_listing(
    listing: BenchListing, latest: dict[tuple[str, str, str, str], BenchRun]
) -> list[str]:
    registre = list(list_engine_refs())
    seen = set(registre)
    extras: list[str] = []
    for category, dataset_id, ref, _effort in latest:
        if category == listing.category and dataset_id == listing.id and ref not in seen:
            extras.append(ref)
            seen.add(ref)
    return registre + extras


def _bank_pack_entry(
    listing: BenchListing,
    latest: dict[tuple[str, str, str, str], BenchRun],
    *,
    refs: list[str] | None = None,
) -> dict[str, Any] | None:
    rows: list[tuple[str, str, BenchRun]] = []
    for ref in refs if refs is not None else list(list_engine_refs()):
        for effort in EFFORTS:
            row = latest.get((listing.category, listing.id, ref, effort))
            if row is not None:
                rows.append((ref, effort, row))
    if not rows:
        return None
    dataset = resolve_bench_dataset(listing.category, listing.id)
    efforts = [
        {
            "search_effort": effort,
            "run_id": row.id,
            "engine_ref": ref,
            "duration_seconds": row.duration_seconds,
            "below_manuel": _below_manuel(row),
            "model": _cycle_slice(dataset, row.assignments),
            "deltas": dict(row.deltas),
            "trace": _trace_json(row),
        }
        for ref, effort, row in rows
    ]
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
    origin: str | None = None,
) -> dict[str, Any]:
    require_admin(authorization)
    require_database()
    if scope not in EXPORT_SCOPES:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    origin_filter = _parse_origin(origin)
    if scope == "dataset":
        origin_filter = None
    listed = {(item.category, item.id): item for item in _all_listings()}
    datasets: list[dict[str, Any]] = []
    if scope == "bank":
        latest = _latest_runs_by_quad()
        for item in _all_listings(origin_filter):
            entry = _bank_pack_entry(item, latest)
            if entry is not None:
                datasets.append(entry)
    elif scope == "dataset":
        if not isinstance(category, str) or not category or not isinstance(dataset_id, str) or not dataset_id:
            raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
        listing = listed.get((category, dataset_id))
        if listing is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING)
        latest = _latest_runs_by_quad()
        entry = _bank_pack_entry(listing, latest, refs=_engine_refs_for_listing(listing, latest))
        if entry is None:
            raise HTTPException(status_code=404, detail=DETAIL_BENCH_RUN_MISSING)
        datasets.append(entry)
    else:
        grouped = _latest_current_runs_map()
        for item in _all_listings(origin_filter):
            latest = grouped.get((item.category, item.id)) or {}
            if not latest:
                continue
            if not any(_below_manuel(row) for row in latest.values()):
                continue
            datasets.append(_dataset_pack_entry(item, latest))
    ref = get_effective_bench_engine_ref()
    return {
        "export_version": 1,
        "kind": "bench-pack",
        "engine_ref": ref,
        "app_version": ref,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "datasets": datasets,
    }


def _gap_targets(origin: str | None = None) -> list[tuple[str, str, str, str]]:
    latest = _latest_runs_by_quad()
    holes: list[tuple[str, str, str, str]] = []
    for item in _all_listings(origin):
        if not _target_has_salle(item.category, item.id):
            continue
        for effort in EFFORTS:
            for ref in list_engine_refs():
                row = latest.get((item.category, item.id, ref, effort))
                if row is None or not _trace_complete(row.trace):
                    holes.append((item.category, item.id, effort, ref))
    return holes


def _queued_response(batch_id: str, job_ids: list[str]) -> JSONResponse:
    return JSONResponse(
        status_code=202,
        content={
            "batch_id": batch_id,
            "job_ids": job_ids,
            "total": len(job_ids),
            "status": "queued",
        },
    )


def post_run(authorization: str | None, body: dict[str, Any]) -> dict[str, Any] | JSONResponse:
    require_admin(authorization)
    require_database()
    if isinstance(body, dict) and body.get("scope") == "gaps":
        origin = _parse_origin(body.get("origin"))
        batch_id = secrets.token_urlsafe(12)
        targets = _gap_targets(origin)
        if not targets:
            return {"batch_id": batch_id, "job_ids": [], "total": 0, "status": "done"}
        job_ids = [
            _enqueue_bench_job(category, dataset_id, effort, ref, batch_id)
            for category, dataset_id, effort, ref in targets
        ]
        return _queued_response(batch_id, job_ids)
    scope, effort, targets, ref_to_use = _parse_run_body(body)
    async_run = scope in ("all", "category") or effort == "maximal"
    if async_run:
        batch_id = secrets.token_urlsafe(12)
        job_ids = [
            _enqueue_bench_job(category, dataset_id, effort, ref_to_use, batch_id)
            for category, dataset_id in targets
        ]
        return _queued_response(batch_id, job_ids)
    category, dataset_id = targets[0]
    try:
        outcome = run_bench_on(
            resolve_bench_dataset(category, dataset_id),
            SearchEffort(effort),
            engine_ref=ref_to_use,
        )
    except UnknownBenchDataset as exc:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_MISSING) from exc
    row = persist_bench_outcome(outcome)
    return {"runs": [_run_summary(row)]}


MIX0_EXPERTS = 4


def _effort_cap(effort: str, engine_ref: str | None = None) -> float:
    base = float(SEARCH_SECONDS[SearchEffort(effort)])
    if engine_ref == "mix-0":
        if effort in ("minimal", "optimized"):
            return MIX0_EXPERTS * base
        return base
    return base


def _remaining_running(job: BenchJob, now: datetime) -> float:
    cap = _effort_cap(job.search_effort, job.engine_ref)
    if job.started_at is None:
        return cap
    started = job.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return max(0.0, cap - (now - started).total_seconds())


def _eta_max_seconds(jobs: list[BenchJob], now: datetime) -> int:
    running = [job for job in jobs if job.status == "running"]
    queued = sorted(
        (job for job in jobs if job.status == "queued"),
        key=lambda job: job.created_at,
    )
    if not running and not queued:
        return 0
    n = max(1, len(running))
    loads = [0.0] * n
    for index, job in enumerate(running):
        loads[index] = _remaining_running(job, now)
    for index, job in enumerate(queued):
        loads[index % n] += _effort_cap(job.search_effort, job.engine_ref)
    return int(max(loads))


def _batch_body(batch_id: str, jobs: list[BenchJob], now: datetime) -> dict[str, Any]:
    total = len(jobs)
    queued = sum(1 for job in jobs if job.status == "queued")
    running = sum(1 for job in jobs if job.status == "running")
    done = sum(1 for job in jobs if job.status == "done")
    failed = sum(1 for job in jobs if job.status == "failed")
    cancelled = sum(1 for job in jobs if job.status == "cancelled")
    pct = 100.0 if total == 0 else 100.0 * (done + failed + cancelled) / total
    return {
        "batch_id": batch_id,
        "total": total,
        "queued": queued,
        "running": running,
        "done": done,
        "failed": failed,
        "pct": pct,
        "eta_max_seconds": _eta_max_seconds(jobs, now),
    }


def get_batch(authorization: str | None, batch_id: str) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        jobs = list(db.scalars(select(BenchJob).where(BenchJob.batch_id == batch_id)))
    if not jobs:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_BATCH_MISSING)
    return _batch_body(batch_id, jobs, datetime.now(timezone.utc))


def get_active_batch(authorization: str | None) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        jobs = list(db.scalars(select(BenchJob).where(BenchJob.batch_id.is_not(None))))
    grouped: dict[str, list[BenchJob]] = {}
    for job in jobs:
        assert job.batch_id is not None
        grouped.setdefault(job.batch_id, []).append(job)
    incomplete: list[tuple[datetime, str, list[BenchJob]]] = []
    for batch_id, group in grouped.items():
        finished = sum(1 for job in group if job.status in ("done", "failed", "cancelled"))
        if finished < len(group):
            newest = max(job.created_at for job in group)
            incomplete.append((newest, batch_id, group))
    if not incomplete:
        raise HTTPException(status_code=404, detail=DETAIL_BENCH_BATCH_MISSING)
    incomplete.sort(key=lambda item: item[0], reverse=True)
    _, batch_id, group = incomplete[0]
    return _batch_body(batch_id, group, datetime.now(timezone.utc))


def cancel_batch(authorization: str | None, batch_id: str) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        result = db.execute(
            update(BenchJob)
            .where(BenchJob.batch_id == batch_id)
            .where(BenchJob.status == "queued")
            .values(status="cancelled")
        )
        count = result.rowcount
    if count == 0:
        with session_scope() as db:
            exists = db.scalar(select(BenchJob.id).where(BenchJob.batch_id == batch_id).limit(1))
            if exists is None:
                raise HTTPException(status_code=404, detail="batch introuvable")
    return {"batch_id": batch_id, "cancelled_count": count}
