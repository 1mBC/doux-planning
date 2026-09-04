from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_company_restaurant_id, require_database
from doux_planning.api.context import _load_company, _state_from_rows
from doux_planning.api.db import Company, session_scope
from doux_planning.context import TeamNotReady, generate_team
from doux_planning.planning import PublishedCycle
from doux_planning.types import SearchEffort, Team

DETAIL_NOT_READY = "Cette équipe n'est pas prête à calculer."
TEAMS = ("salle", "cuisine")
EFFORTS = ("minimal", "optimized", "maximal")


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


def _cycle_json(published: PublishedCycle | None) -> dict[str, Any] | None:
    if published is None:
        return None
    result = published.result
    return {
        "assignments": [_shift_json(shift) for shift in result.assignments],
        "warnings": [_warning_json(warning) for warning in result.warnings],
    }


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
    company, _fiches = _load_company(restaurant_id)
    return {"published": _stored_published(company.published_cycles)}


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
    stored[team.value] = _cycle_json(state.published_cycles[team])
    _persist_published(restaurant_id, stored)
    return {
        "team": team.value,
        "search_effort": search.value,
        "published": stored,
    }
