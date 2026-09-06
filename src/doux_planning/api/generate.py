from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_admin, require_company_restaurant_id, require_database
from doux_planning.api.context import _load_company, _state_from_rows
from doux_planning.api.db import Company, GenerateLog, RestaurateurAccount, session_scope
from doux_planning.context import CycleRecap, RecapCell, TeamNotReady, cycle_recap, generate_team
from doux_planning.planning import PublishedCycle, RestaurantState
from doux_planning.types import SearchEffort, Team

DETAIL_NOT_READY = "Cette équipe n'est pas prête à calculer."
TEAMS = ("salle", "cuisine")
EFFORTS = ("minimal", "optimized", "maximal")
RECAP_KEYS = ("stats", "legal_cols", "legal_rows", "wish_cols", "wish_rows")


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


def _has_recap(blob: Any) -> bool:
    return isinstance(blob, dict) and all(key in blob for key in RECAP_KEYS)


def _blob_with_recap(state: RestaurantState, team: Team, blob: Any) -> dict[str, Any] | None:
    if blob is None:
        return None
    if _has_recap(blob):
        return blob
    from doux_planning.api.live_sandbox import _published_from_json

    state.published_cycles[team] = _published_from_json(state, team, blob)
    return _team_cycle_json(state, team)


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
    if all(blob is None or _has_recap(blob) for blob in stored.values()):
        return {"published": stored}
    state = _state_from_rows(company, fiches)
    published = {
        "salle": _blob_with_recap(state, Team.SALLE, stored["salle"]),
        "cuisine": _blob_with_recap(state, Team.CUISINE, stored["cuisine"]),
    }
    _persist_published(restaurant_id, published)
    return {"published": published}


def post_generate(authorization: str | None, body: dict[str, Any]) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    team, search = _parse_generate(body)
    company, fiches = _load_company(restaurant_id)
    stored = _stored_published(company.published_cycles)
    state = _state_from_rows(company, fiches)
    try:
        generate_team(state, team, search)
    except TeamNotReady as exc:
        raise HTTPException(status_code=409, detail=DETAIL_NOT_READY) from exc
    published = {
        "salle": (
            _team_cycle_json(state, Team.SALLE)
            if team == Team.SALLE
            else _blob_with_recap(state, Team.SALLE, stored["salle"])
        ),
        "cuisine": (
            _team_cycle_json(state, Team.CUISINE)
            if team == Team.CUISINE
            else _blob_with_recap(state, Team.CUISINE, stored["cuisine"])
        ),
    }
    _persist_published(restaurant_id, published)
    cycle = published[team.value] or {}
    _log_generate(
        restaurant_id,
        restaurant_name=company.name or "",
        team=team.value,
        warnings=list(cycle.get("warnings") or []),
    )
    return {
        "team": team.value,
        "search_effort": search.value,
        "published": published,
    }


def _log_generate(restaurant_id: str, *, restaurant_name: str, team: str, warnings: list[Any]) -> None:
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
                warnings=warnings,
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
                    "warnings": list(row.warnings or []),
                }
                for row in rows
            ]
        }
