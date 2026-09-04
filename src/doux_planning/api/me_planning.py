from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from doux_planning.api.auth import require_database, require_employee_session
from doux_planning.api.context import _load_company, _state_from_rows
from doux_planning.api.generate import _shift_json
from doux_planning.api.live_sandbox import TEAMS, _published_from_json
from doux_planning.context import employee_board
from doux_planning.invites import UnknownEmployee
from doux_planning.staff import Employee, Unavailability


def _hydrate_published(state, company) -> None:
    raw = company.published_cycles or {}
    for team in TEAMS:
        state.published_cycles[team] = _published_from_json(state, team, raw.get(team.value))


def _employee_json(person: Employee) -> dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "role": {"name": person.role.name, "level": person.role.level, "team": person.role.team.value},
        "team": person.team.value,
    }


def _unavailability_json(item: Unavailability) -> dict[str, Any]:
    return {
        "weekday": item.weekday,
        "every_morning": item.every_morning,
        "every_evening": item.every_evening,
        "service_id": item.service_id,
    }


def get_me_planning(authorization: str | None) -> dict[str, Any]:
    require_database()
    restaurant_id, employee_id = require_employee_session(authorization)
    company, fiches = _load_company(restaurant_id)
    state = _state_from_rows(company, fiches)
    _hydrate_published(state, company)
    try:
        board = employee_board(state, employee_id)
    except UnknownEmployee as exc:
        raise HTTPException(status_code=401, detail="Session invalide.") from exc
    teammates = [person for person in state.employees if person.team == board.team]
    return {
        "employee_id": board.employee_id,
        "team": board.team.value,
        "employees": [_employee_json(person) for person in teammates],
        "assignments": [_shift_json(shift) for shift in board.assignments],
        "contract": {
            "weekly": board.contract.weekly,
            "assigned": board.contract.assigned,
            "ok": board.contract.ok,
        },
        "wishes": [{"key": wish.key.value, "held": wish.held} for wish in board.wishes],
        "unavailabilities": [_unavailability_json(item) for item in board.unavailabilities],
    }
