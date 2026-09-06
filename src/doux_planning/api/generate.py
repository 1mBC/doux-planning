from __future__ import annotations

import secrets
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_admin, require_company_restaurant_id, require_database
from doux_planning.api.context import _load_company, _state_from_rows
from doux_planning.api.db import Company, GenerateJob, GenerateLog, RestaurateurAccount, session_scope
from doux_planning.context import CycleRecap, RecapCell, TeamNotReady, cycle_recap, generate_team, team_ready
from doux_planning.planning import PublishedCycle, RestaurantState
from doux_planning.types import SearchEffort, Team

DETAIL_NOT_READY = "Cette équipe n'est pas prête à calculer."
DETAIL_JOB_RUNNING = "Un calcul maximal est déjà en cours."
DETAIL_JOB_MISSING = "Calcul introuvable."
TEAMS = ("salle", "cuisine")
EFFORTS = ("minimal", "optimized", "maximal")
ACTIVE_JOB_STATUSES = ("queued", "running")
RECAP_KEYS = ("stats", "legal_cols", "legal_rows", "wish_cols", "wish_rows")
MAXIMAL_ESTIMATED_SECONDS = 600
EFFORT_RANK = {"minimal": 1, "optimized": 2, "maximal": 3}


def iso_log(event: str, **fields: Any) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    extras = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    print(f"{stamp} {event}" + (f" {extras}" if extras else ""), flush=True)


def _empty_versions() -> dict[str, Any]:
    return {
        "versions": {"minimal": None, "optimized": None, "maximal": None},
        "latest": None,
    }


def compute_latest(versions: dict[str, Any]) -> str | None:
    best: tuple[str, int, str] | None = None
    for effort in EFFORTS:
        cycle = versions.get(effort)
        if not cycle:
            continue
        stamp = str(cycle.get("generated_at") or "")
        candidate = (stamp, EFFORT_RANK[effort], effort)
        if best is None or candidate > best:
            best = candidate
    return best[2] if best else None


def _has_recap(blob: Any) -> bool:
    return isinstance(blob, dict) and all(key in blob for key in RECAP_KEYS)


def _ensure_cycle_recap(state: RestaurantState, team: Team, cycle: dict[str, Any]) -> dict[str, Any]:
    if _has_recap(cycle):
        return cycle
    from doux_planning.api.live_sandbox import _published_from_json

    state.published_cycles[team] = _published_from_json(state, team, cycle)
    filled = _team_cycle_json(state, team)
    if filled is None:
        return cycle
    if "generated_at" in cycle:
        filled["generated_at"] = cycle["generated_at"]
    if "search_effort" in cycle:
        filled["search_effort"] = cycle["search_effort"]
    if "duration_seconds" in cycle:
        filled["duration_seconds"] = cycle["duration_seconds"]
    return filled


def normalize_team_published(
    blob: Any,
    state: RestaurantState | None = None,
    team: Team | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    if blob is None:
        return None, False
    if isinstance(blob, dict) and "versions" in blob:
        raw_versions = blob.get("versions") or {}
        out = _empty_versions()
        dirty = set(raw_versions) != set(EFFORTS) or "latest" not in blob
        for effort in EFFORTS:
            cycle = raw_versions.get(effort)
            if cycle is None:
                continue
            if state is not None and team is not None and not _has_recap(cycle):
                cycle = _ensure_cycle_recap(state, team, cycle)
                dirty = True
            out["versions"][effort] = cycle
        latest = blob.get("latest")
        if latest not in EFFORTS:
            latest = compute_latest(out["versions"])
            dirty = True
        out["latest"] = latest
        return out, dirty
    if isinstance(blob, dict) and "assignments" in blob:
        cycle = dict(blob)
        if state is not None and team is not None and not _has_recap(cycle):
            cycle = _ensure_cycle_recap(state, team, cycle)
        cycle.pop("generated_at", None)
        cycle["search_effort"] = "optimized"
        return {
            "versions": {"minimal": None, "optimized": cycle, "maximal": None},
            "latest": "optimized",
        }, True
    return None, False


def put_generated_slot(
    stored_blob: Any,
    effort: str,
    cycle: dict[str, Any],
    generated_at: str,
    duration_seconds: float,
    state: RestaurantState | None = None,
    team: Team | None = None,
) -> dict[str, Any]:
    pack, _ = normalize_team_published(stored_blob, state, team)
    if pack is None:
        pack = _empty_versions()
    slot = dict(cycle)
    slot["generated_at"] = generated_at
    slot["search_effort"] = effort
    slot["duration_seconds"] = duration_seconds
    pack["versions"][effort] = slot
    pack["latest"] = compute_latest(pack["versions"])
    return pack


def overwrite_slot_keep_generated_at(
    stored_blob: Any,
    effort: str,
    cycle: dict[str, Any],
    state: RestaurantState | None = None,
    team: Team | None = None,
) -> dict[str, Any]:
    pack, _ = normalize_team_published(stored_blob, state, team)
    if pack is None:
        pack = _empty_versions()
    previous = pack["versions"].get(effort) or {}
    slot = dict(cycle)
    if "generated_at" in previous:
        slot["generated_at"] = previous["generated_at"]
    else:
        slot.pop("generated_at", None)
    if "duration_seconds" in previous:
        slot["duration_seconds"] = previous["duration_seconds"]
    else:
        slot.pop("duration_seconds", None)
    slot["search_effort"] = effort
    pack["versions"][effort] = slot
    others = [item for item in EFFORTS if item != effort and pack["versions"].get(item)]
    if not others:
        pack["latest"] = effort
    return pack


def latest_cycle_blob(pack: dict[str, Any] | None) -> dict[str, Any] | None:
    if pack is None or pack.get("latest") not in EFFORTS:
        return None
    return pack["versions"].get(pack["latest"])


def normalize_published(
    stored: dict[str, Any],
    state: RestaurantState | None = None,
) -> tuple[dict[str, Any], bool]:
    dirty = False
    published = {"salle": None, "cuisine": None}
    for key, team in (("salle", Team.SALLE), ("cuisine", Team.CUISINE)):
        pack, changed = normalize_team_published(stored.get(key), state, team)
        published[key] = pack
        dirty = dirty or changed
    return published, dirty


def _empty_published() -> dict[str, Any]:
    return {"salle": None, "cuisine": None}


def _stored_published(raw: dict[str, Any] | None) -> dict[str, Any]:
    payload = raw or {}
    return {"salle": payload.get("salle"), "cuisine": payload.get("cuisine")}


def _shift_json(shift: Any) -> dict[str, Any]:
    return {
        "employee_id": shift.employee_id,
        "day_index": shift.day_index,
        "weekday": shift.weekday,
        "service_id": shift.service_id,
        "team": shift.team.value,
        "start_minutes": shift.start_minutes,
        "end_minutes": shift.end_minutes,
        "post_level": shift.post_level,
        "duration_hours": shift.duration_hours,
    }


def _warning_json(warning: Any) -> dict[str, Any]:
    return {
        "severity": warning.severity.value,
        "code": warning.code,
        "message": warning.message,
        "employee_id": warning.employee_id,
        "day_index": warning.day_index,
    }


def _cell_json(cell: RecapCell | None) -> dict[str, Any] | None:
    if cell is None:
        return None
    return {"ok": cell.ok, "text": cell.text}


def _row_json(row: Any) -> dict[str, Any]:
    return {
        "name": row.name,
        "employee_id": row.employee_id,
        "cells": {key: _cell_json(value) for key, value in row.cells.items()},
    }


def _cycle_recap_json(recap: CycleRecap) -> dict[str, Any]:
    return {
        "stats": {
            "assignments": recap.stats.assignments,
            "empty": recap.stats.empty,
            "interdit": recap.stats.interdit,
            "below_role": recap.stats.below_role,
            "hours": {
                "assigned": recap.stats.hours.assigned,
                "contracted": recap.stats.hours.contracted,
                "percent": recap.stats.hours.percent,
            },
            "wellbeing": {
                "held": recap.stats.wellbeing.held,
                "total": recap.stats.wellbeing.total,
            },
        },
        "legal_cols": [{"id": col.id, "label_fr": col.label_fr} for col in recap.legal_cols],
        "legal_rows": [_row_json(row) for row in recap.legal_rows],
        "wish_cols": [{"key": col.key, "label": col.label} for col in recap.wish_cols],
        "wish_rows": [_row_json(row) for row in recap.wish_rows],
    }


def _cycle_json(published: PublishedCycle | None, recap: CycleRecap | None = None) -> dict[str, Any] | None:
    if published is None:
        return None
    result = published.result
    body: dict[str, Any] = {
        "assignments": [_shift_json(shift) for shift in result.assignments],
        "warnings": [_warning_json(warning) for warning in result.warnings],
    }
    if recap is not None:
        body.update(_cycle_recap_json(recap))
    return body


def _team_cycle_json(state: RestaurantState, team: Team) -> dict[str, Any] | None:
    published = state.published_cycles.get(team)
    if published is None:
        return None
    return _cycle_json(published, cycle_recap(state, team))


def _blob_with_recap(state: RestaurantState, team: Team, blob: Any) -> dict[str, Any] | None:
    pack, _ = normalize_team_published(blob, state, team)
    return pack


def _parse_generate(body: dict[str, Any]) -> tuple[Team, SearchEffort]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    team_raw = body.get("team")
    if team_raw not in TEAMS:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    effort_raw = body.get("search_effort", SearchEffort.OPTIMIZED.value)
    if effort_raw not in EFFORTS:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    return Team(team_raw), SearchEffort(effort_raw)


def _persist_published(restaurant_id: str, published: dict[str, Any]) -> None:
    with session_scope() as db:
        company = db.get(Company, restaurant_id)
        if company is None:
            raise HTTPException(status_code=401, detail="Session invalide.")
        company.published_cycles = {"salle": published.get("salle"), "cuisine": published.get("cuisine")}
        flag_modified(company, "published_cycles")


def get_cycles(authorization: str | None) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    stored = _stored_published(company.published_cycles)
    state = None
    if any(blob is not None for blob in stored.values()):
        state = _state_from_rows(company, fiches)
    published, dirty = normalize_published(stored, state)
    if dirty:
        _persist_published(restaurant_id, published)
    return {"published": published}


def _published_after_generate(
    state: RestaurantState,
    team: Team,
    stored: dict[str, Any],
    effort: str,
    generated_at: str,
    duration_seconds: float,
) -> dict[str, Any]:
    cycle = _team_cycle_json(state, team)
    published: dict[str, Any] = {}
    for key, other in (("salle", Team.SALLE), ("cuisine", Team.CUISINE)):
        if other == team:
            published[key] = put_generated_slot(
                stored.get(key),
                effort,
                cycle or {},
                generated_at,
                duration_seconds,
                state,
                team,
            )
        else:
            pack, _ = normalize_team_published(stored.get(key), state, other)
            published[key] = pack
    return published


def _enqueue_maximal(restaurant_id: str, team: Team) -> str:
    job_id = secrets.token_urlsafe(12)
    try:
        with session_scope() as db:
            existing = db.scalars(
                select(GenerateJob).where(
                    GenerateJob.restaurant_id == restaurant_id,
                    GenerateJob.team == team.value,
                    GenerateJob.status.in_(ACTIVE_JOB_STATUSES),
                )
            ).first()
            if existing is not None:
                raise HTTPException(status_code=409, detail=DETAIL_JOB_RUNNING)
            db.add(
                GenerateJob(
                    id=job_id,
                    restaurant_id=restaurant_id,
                    team=team.value,
                    search_effort=SearchEffort.MAXIMAL.value,
                    status="queued",
                    estimated_seconds=MAXIMAL_ESTIMATED_SECONDS,
                    error=None,
                    created_at=datetime.now(timezone.utc),
                )
            )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=DETAIL_JOB_RUNNING) from exc
    return job_id


def _job_payload(job: GenerateJob, published: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "job_id": job.id,
        "team": job.team,
        "search_effort": job.search_effort,
        "status": job.status,
        "estimated_seconds": job.estimated_seconds,
    }
    if job.status == "failed" and job.error:
        body["error"] = job.error
    if job.status == "done" and published is not None:
        body["published"] = published
    return body


def get_generate_job(authorization: str | None, job_id: str) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    with session_scope() as db:
        job = db.get(GenerateJob, job_id)
        if job is None or job.restaurant_id != restaurant_id:
            raise HTTPException(status_code=404, detail=DETAIL_JOB_MISSING)
        status = job.status
        payload = _job_payload(job)
    if status in ("done", "failed"):
        iso_log("generate job", job_id=job_id, status=status)
    if status == "done":
        company, fiches = _load_company(restaurant_id)
        stored = _stored_published(company.published_cycles)
        state = _state_from_rows(company, fiches) if any(stored.values()) else None
        published, dirty = normalize_published(stored, state)
        if dirty:
            _persist_published(restaurant_id, published)
        payload["published"] = published
    return payload


def post_generate(authorization: str | None, body: dict[str, Any]) -> dict[str, Any] | JSONResponse:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    team, search = _parse_generate(body)
    company, fiches = _load_company(restaurant_id)
    stored = _stored_published(company.published_cycles)
    state = _state_from_rows(company, fiches)
    if search == SearchEffort.MAXIMAL:
        if not team_ready(state, team):
            raise HTTPException(status_code=409, detail=DETAIL_NOT_READY)
        job_id = _enqueue_maximal(restaurant_id, team)
        iso_log("generate 202", job_id=job_id, team=team.value)
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "team": team.value,
                "search_effort": SearchEffort.MAXIMAL.value,
                "status": "queued",
                "estimated_seconds": MAXIMAL_ESTIMATED_SECONDS,
            },
        )
    started = time.perf_counter()
    try:
        generate_team(state, team, search)
    except TeamNotReady as exc:
        raise HTTPException(status_code=409, detail=DETAIL_NOT_READY) from exc
    duration_seconds = max(0.0, time.perf_counter() - started)
    generated_at = datetime.now(timezone.utc).isoformat()
    published = _published_after_generate(state, team, stored, search.value, generated_at, duration_seconds)
    _persist_published(restaurant_id, published)
    slot = ((published[team.value] or {}).get("versions") or {}).get(search.value) or {}
    _log_generate(
        restaurant_id,
        restaurant_name=company.name or "",
        team=team.value,
        search_effort=search.value,
        duration_seconds=duration_seconds,
        warnings=list(slot.get("warnings") or []),
        employees=state.employees,
    )
    return {
        "team": team.value,
        "search_effort": search.value,
        "published": published,
    }


def persist_maximal_result(
    restaurant_id: str,
    team: Team,
    *,
    generate_fn: Any = generate_team,
) -> dict[str, Any]:
    company, fiches = _load_company(restaurant_id)
    stored = _stored_published(company.published_cycles)
    state = _state_from_rows(company, fiches)
    started = time.perf_counter()
    generate_fn(state, team, SearchEffort.MAXIMAL)
    duration_seconds = max(0.0, time.perf_counter() - started)
    generated_at = datetime.now(timezone.utc).isoformat()
    published = _published_after_generate(
        state,
        team,
        stored,
        SearchEffort.MAXIMAL.value,
        generated_at,
        duration_seconds,
    )
    _persist_published(restaurant_id, published)
    slot = ((published[team.value] or {}).get("versions") or {}).get(SearchEffort.MAXIMAL.value) or {}
    _log_generate(
        restaurant_id,
        restaurant_name=company.name or "",
        team=team.value,
        search_effort=SearchEffort.MAXIMAL.value,
        duration_seconds=duration_seconds,
        warnings=list(slot.get("warnings") or []),
        employees=state.employees,
    )
    return published


def _employee_name_at_log(employees: Any, employee_id: str | None) -> str | None:
    if not employee_id:
        return None
    for person in employees or []:
        if getattr(person, "id", None) == employee_id:
            return getattr(person, "name", None)
    return None


def _log_warnings(warnings: list[Any], employees: Any) -> list[dict[str, Any]]:
    logged: list[dict[str, Any]] = []
    for warning in warnings:
        if isinstance(warning, dict):
            item = {
                "severity": warning.get("severity"),
                "code": warning.get("code"),
                "message": warning.get("message"),
                "employee_id": warning.get("employee_id"),
                "day_index": warning.get("day_index"),
            }
        else:
            item = _warning_json(warning)
        item["employee_name"] = _employee_name_at_log(employees, item.get("employee_id"))
        logged.append(item)
    return logged


def _log_generate(
    restaurant_id: str,
    *,
    restaurant_name: str,
    team: str,
    search_effort: str,
    duration_seconds: float,
    warnings: list[Any],
    employees: Any,
) -> None:
    with session_scope() as db:
        account = db.scalars(
            select(RestaurateurAccount).where(RestaurateurAccount.restaurant_id == restaurant_id)
        ).first()
        if account is None:
            return
        db.add(
            GenerateLog(
                id=secrets.token_urlsafe(12),
                created_at=datetime.now(timezone.utc),
                email=account.email,
                restaurant_name=restaurant_name,
                team=team,
                search_effort=search_effort,
                duration_seconds=duration_seconds,
                warnings=_log_warnings(warnings, employees),
            )
        )


def list_generate_logs(authorization: str | None) -> dict[str, Any]:
    require_admin(authorization)
    with session_scope() as db:
        rows = db.scalars(select(GenerateLog).order_by(GenerateLog.created_at.desc(), GenerateLog.id.desc())).all()
        return {
            "entries": [
                {
                    "id": row.id,
                    "created_at": row.created_at.isoformat(),
                    "email": row.email,
                    "restaurant_name": row.restaurant_name,
                    "team": row.team,
                    "search_effort": row.search_effort,
                    "duration_seconds": row.duration_seconds,
                    "warnings": list(row.warnings or []),
                }
                for row in rows
            ]
        }
