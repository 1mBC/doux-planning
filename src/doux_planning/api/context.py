from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.auth import (
    DETAIL_INVALID_FIELDS,
    DETAIL_FICHE_LINKED,
    require_company_restaurant_id,
    require_database,
    _fiche_to_employee,
)
from doux_planning.api.db import (
    AccountEmail,
    AuthSession,
    Company,
    EmployeeAccountRow,
    StaffFiche,
    session_scope,
)
from doux_planning.api.wellbeing_codec import (
    coerce_unavailabilities,
    coerce_wellbeing,
    unavailability_from_json,
    unavailability_to_json,
    wellbeing_from_json,
    wellbeing_to_json,
)
from doux_planning.context import (
    empty_restaurant,
    seed_example_context,
    set_restaurant_name,
    set_role_ladder,
    set_services,
    set_typical_week,
    team_ready,
    upsert_employee,
    upsert_service_type,
    week_label_scheme,
)
from doux_planning.invites import RestaurantIdentity
from doux_planning.planning import RestaurantState
from doux_planning.staff import Employee, Role, RoleLadder
from doux_planning.structures import (
    ArrivalWave,
    DepartureWave,
    RestaurantHours,
    ServiceType,
    TypicalWeek,
    TypicalWeekCell,
)
from doux_planning.types import DEFAULT_MIN_SHIFT_HOURS, Team, WEEKDAYS

TEAMS = (Team.SALLE, Team.CUISINE)
SERVICE_IDS = frozenset({"morning", "midday", "evening"})
FORBIDDEN_PATCH = frozenset({"legal_context_id", "company_code", "ready", "week_labels"})
EXPORT_SECTIONS = ("name", "services", "ladders", "employees", "types", "typical_week")


def _invalid() -> HTTPException:
    return HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)


def _load_company(restaurant_id: str) -> tuple[Company, list[StaffFiche]]:
    with session_scope() as db:
        company = db.get(Company, restaurant_id)
        if company is None:
            raise HTTPException(status_code=401, detail="Session invalide.")
        fiches = list(db.scalars(select(StaffFiche).where(StaffFiche.company_id == company.id)))
        services = list(company.services or [])
        for row in fiches:
            try:
                wellbeing_json = wellbeing_to_json(coerce_wellbeing(row.wellbeing))
                unavail_json = [
                    unavailability_to_json(item)
                    for item in coerce_unavailabilities(row.unavailabilities, services)
                ]
            except (ValueError, KeyError, TypeError):
                continue
            if row.wellbeing != wellbeing_json or list(row.unavailabilities or []) != unavail_json:
                row.wellbeing = wellbeing_json
                row.unavailabilities = unavail_json
                flag_modified(row, "wellbeing")
                flag_modified(row, "unavailabilities")
        db.flush()
        db.expunge(company)
        for row in fiches:
            db.expunge(row)
        return company, fiches


def _state_from_rows(company: Company, fiches: list[StaffFiche]) -> RestaurantState:
    state = empty_restaurant(company.id)
    state.identity = RestaurantIdentity(
        id=company.id,
        invite_code=company.invite_code,
        linked_employee_ids=frozenset(company.linked_employee_ids or []),
        name=company.name or "",
        legal_context_id=company.legal_context_id or "france",
    )
    try:
        services = list(company.services or [])
        if services:
            set_services(state, services)
        ladders = company.ladders or {}
        for team in TEAMS:
            payload = ladders.get(team.value)
            if payload:
                set_role_ladder(state, _ladder_from_json(team, payload))
        for row in fiches:
            upsert_employee(state, _fiche_to_employee(row, company.services))
        for item in company.types or []:
            upsert_service_type(state, _type_from_json(item))
        week = _week_from_json(company.typical_week or {})
        if week is not None:
            set_typical_week(state, week)
        if company.hours:
            state.hours = _hours_from_json(company.hours)
    except (ValueError, KeyError, TypeError) as exc:
        raise _invalid() from exc
    return state


def _ladder_from_json(team: Team, payload: Any) -> RoleLadder:
    if not isinstance(payload, dict):
        raise ValueError("invalid ladder")
    if payload.get("substitution_explained") is not True:
        raise ValueError("substitution_explained must be true")
    roles_raw = payload.get("roles")
    if not isinstance(roles_raw, list) or not roles_raw:
        raise ValueError("ladder roles required")
    roles = []
    for item in roles_raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("invalid role")
        level = item.get("level")
        if not isinstance(level, int) or isinstance(level, bool) or level < 1:
            raise ValueError("invalid level")
        roles.append(Role(item["name"], level, team))
    return RoleLadder(team, tuple(roles), substitution_explained=True)


def _type_from_json(item: Any) -> ServiceType:
    if not isinstance(item, dict):
        raise ValueError("invalid type")
    team = Team(item["team"])
    service_id = item.get("service_id")
    if service_id not in SERVICE_IDS:
        raise ValueError("invalid service")
    arrivals = []
    for wave in item.get("arrivals") or []:
        if not isinstance(wave, dict):
            raise ValueError("invalid arrival")
        levels = wave.get("post_levels")
        if not isinstance(levels, list) or not levels:
            raise ValueError("invalid arrival")
        arrivals.append(ArrivalWave(int(wave["time_minutes"]), tuple(int(level) for level in levels)))
    departures = []
    for wave in item.get("departures") or []:
        if not isinstance(wave, dict):
            raise ValueError("invalid departure")
        remaining = wave.get("remaining_post_levels")
        if not isinstance(remaining, list):
            raise ValueError("invalid departure")
        departures.append(
            DepartureWave(int(wave["time_minutes"]), tuple(int(level) for level in remaining))
        )
    return ServiceType(
        id=str(item["id"]),
        name=str(item["name"]),
        team=team,
        service_id=service_id,
        arrivals=tuple(arrivals),
        departures=tuple(departures),
    )


def _week_from_json(payload: Any) -> TypicalWeek | None:
    if not payload:
        return None
    if not isinstance(payload, dict):
        raise ValueError("invalid typical_week")
    cells: list[TypicalWeekCell] = []
    any_grid = False
    for team in TEAMS:
        grid = payload.get(team.value)
        if grid is None:
            continue
        any_grid = True
        if not isinstance(grid, list):
            raise ValueError("invalid typical_week")
        for item in grid:
            if not isinstance(item, dict):
                raise ValueError("invalid cell")
            weekday = item.get("weekday")
            service_id = item.get("service_id")
            closed = item.get("closed")
            if weekday not in WEEKDAYS or service_id not in SERVICE_IDS or not isinstance(closed, bool):
                raise ValueError("invalid cell")
            type_id = item.get("type_id")
            if type_id is not None and not isinstance(type_id, str):
                raise ValueError("invalid cell")
            if closed and type_id is not None:
                raise ValueError("closed cell must have null type")
            cells.append(
                TypicalWeekCell(
                    weekday=weekday,
                    service_id=service_id,
                    type_id=type_id,
                    closed=closed,
                    team=team,
                )
            )
    if not any_grid:
        return None
    return TypicalWeek(cells=tuple(cells))


def _hours_from_json(raw: Any) -> RestaurantHours:
    if not isinstance(raw, dict):
        raise ValueError("invalid hours")
    return RestaurantHours(
        mode=raw["mode"],
        services=tuple(raw["services"]),
        closed_weekdays=frozenset(raw.get("closed_weekdays") or ()),
        closed_services=frozenset(raw.get("closed_services") or ()),
    )


def _hours_to_json(hours: RestaurantHours | None) -> dict[str, Any] | None:
    if hours is None:
        return None
    return {
        "mode": hours.mode,
        "services": list(hours.services),
        "closed_weekdays": sorted(hours.closed_weekdays),
        "closed_services": sorted(hours.closed_services),
    }


def _employee_from_json(item: Any, existing_token: str | None) -> Employee:
    if not isinstance(item, dict):
        raise ValueError("invalid employee")
    if "max_evenings_per_week" in item or "max_mornings_per_week" in item:
        raise ValueError("legacy max_evenings_per_week / max_mornings_per_week are not accepted")
    team = Team(item["team"])
    role_raw = item.get("role")
    if not isinstance(role_raw, dict):
        raise ValueError("invalid role")
    role = Role(str(role_raw["name"]), int(role_raw["level"]), Team(role_raw["team"]))
    hours = item.get("contractual_hours_per_week")
    if not isinstance(hours, (int, float)) or isinstance(hours, bool):
        raise ValueError("invalid hours")
    min_shift = item.get("min_shift_hours", DEFAULT_MIN_SHIFT_HOURS)
    if not isinstance(min_shift, (int, float)) or isinstance(min_shift, bool):
        raise ValueError("invalid min_shift")
    unavail_raw = item.get("unavailabilities") or []
    if not isinstance(unavail_raw, list):
        raise ValueError("invalid unavailabilities")
    unavailabilities = tuple(unavailability_from_json(entry) for entry in unavail_raw)
    wellbeing = wellbeing_from_json(item.get("wellbeing"))
    kwargs: dict[str, Any] = {
        "id": str(item["id"]),
        "name": str(item["name"]),
        "role": role,
        "team": team,
        "contractual_hours_per_week": float(hours),
        "unavailabilities": unavailabilities,
        "wellbeing": wellbeing,
        "min_shift_hours": float(min_shift),
    }
    if existing_token:
        kwargs["invite_token"] = existing_token
    return Employee(**kwargs)


def _serialize_ladder(ladder: RoleLadder | None) -> dict[str, Any] | None:
    if ladder is None:
        return None
    return {
        "roles": [{"name": role.name, "level": role.level} for role in ladder.roles],
        "substitution_explained": True,
    }


def _serialize_type(item: ServiceType) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "team": item.team.value,
        "service_id": item.service_id,
        "arrivals": [
            {"time_minutes": wave.time_minutes, "post_levels": list(wave.post_levels)}
            for wave in item.arrivals
        ],
        "departures": [
            {
                "time_minutes": wave.time_minutes,
                "remaining_post_levels": list(wave.remaining_post_levels),
            }
            for wave in item.departures
        ],
    }


def _serialize_week(week: TypicalWeek | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"salle": None, "cuisine": None}
    if week is None:
        return payload
    grouped: dict[str, list[dict[str, Any]]] = {"salle": [], "cuisine": []}
    for cell in week.cells:
        grouped[cell.team.value].append(
            {
                "weekday": cell.weekday,
                "service_id": cell.service_id,
                "type_id": cell.type_id,
                "closed": cell.closed,
            }
        )
    for team in TEAMS:
        cells = grouped[team.value]
        payload[team.value] = cells or None
    return payload


def _serialize_employee(person: Employee) -> dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "team": person.team.value,
        "role": {"name": person.role.name, "level": person.role.level, "team": person.role.team.value},
        "contractual_hours_per_week": person.contractual_hours_per_week,
        "min_shift_hours": person.min_shift_hours,
        "unavailabilities": [unavailability_to_json(item) for item in person.unavailabilities],
        "wellbeing": wellbeing_to_json(person.wellbeing),
        "invite_token": person.invite_token,
    }


def serialize_context(state: RestaurantState) -> dict[str, Any]:
    return {
        "name": state.identity.name,
        "legal_context_id": state.identity.legal_context_id,
        "company_code": state.identity.invite_code,
        "services": list(state.company_services),
        "ladders": {
            "salle": _serialize_ladder(state.ladders.get(Team.SALLE)),
            "cuisine": _serialize_ladder(state.ladders.get(Team.CUISINE)),
        },
        "employees": [_serialize_employee(person) for person in state.employees],
        "types": [_serialize_type(item) for item in state.service_types],
        "typical_week": _serialize_week(state.typical_week),
        "ready": {
            "salle": team_ready(state, Team.SALLE),
            "cuisine": team_ready(state, Team.CUISINE),
        },
        "week_labels": week_label_scheme(state),
    }


def serialize_export(state: RestaurantState) -> dict[str, Any]:
    context = serialize_context(state)
    employees = []
    for person in context["employees"]:
        row = dict(person)
        row.pop("invite_token", None)
        employees.append(row)
    return {
        "export_version": 1,
        "name": context["name"],
        "services": context["services"],
        "ladders": context["ladders"],
        "employees": employees,
        "types": context["types"],
        "typical_week": context["typical_week"],
    }


def _purge_company_employees(db: Session, restaurant_id: str) -> None:
    accounts = list(db.scalars(select(EmployeeAccountRow).where(EmployeeAccountRow.restaurant_id == restaurant_id)))
    emails = [row.email for row in accounts]
    account_ids = {row.id for row in accounts}
    sessions = list(db.scalars(select(AuthSession).where(AuthSession.restaurant_id == restaurant_id)))
    for session in sessions:
        if session.kind == "employee" or session.account_id in account_ids:
            db.delete(session)
    for row in accounts:
        db.delete(row)
    db.flush()
    for email in emails:
        addr = db.get(AccountEmail, email)
        if addr is not None:
            db.delete(addr)


def _persist_state(restaurant_id: str, state: RestaurantState, *, smash_live: bool = False) -> None:
    with session_scope() as db:
        company = db.get(Company, restaurant_id)
        if company is None:
            raise HTTPException(status_code=401, detail="Session invalide.")
        if smash_live:
            _purge_company_employees(db, restaurant_id)
        company.name = state.identity.name
        company.invite_code = state.identity.invite_code
        company.legal_context_id = state.identity.legal_context_id
        company.linked_employee_ids = sorted(state.identity.linked_employee_ids)
        company.services = list(state.company_services)
        company.ladders = {
            "salle": _serialize_ladder(state.ladders.get(Team.SALLE)),
            "cuisine": _serialize_ladder(state.ladders.get(Team.CUISINE)),
        }
        company.types = [_serialize_type(item) for item in state.service_types]
        company.typical_week = _serialize_week(state.typical_week)
        company.hours = _hours_to_json(state.hours)
        flag_modified(company, "linked_employee_ids")
        flag_modified(company, "services")
        flag_modified(company, "ladders")
        flag_modified(company, "types")
        flag_modified(company, "typical_week")
        flag_modified(company, "hours")
        if smash_live:
            company.published_cycles = {"salle": None, "cuisine": None}
            company.live_sandboxes = {"salle": None, "cuisine": None}
            flag_modified(company, "published_cycles")
            flag_modified(company, "live_sandboxes")
        existing = {
            row.id: row
            for row in db.scalars(select(StaffFiche).where(StaffFiche.company_id == restaurant_id))
        }
        keep = {person.id for person in state.employees}
        for row_id, row in existing.items():
            if row_id not in keep:
                db.delete(row)
        for person in state.employees:
            row = existing.get(person.id)
            payload = dict(
                name=person.name,
                role=person.role.name,
                team=person.team.value,
                invite_token=person.invite_token,
                role_level=person.role.level,
                contractual_hours_per_week=person.contractual_hours_per_week,
                min_shift_hours=person.min_shift_hours,
                unavailabilities=[unavailability_to_json(item) for item in person.unavailabilities],
                wellbeing=wellbeing_to_json(person.wellbeing),
            )
            if row is None:
                db.add(StaffFiche(id=person.id, company_id=restaurant_id, **payload))
            else:
                for key, value in payload.items():
                    setattr(row, key, value)
                flag_modified(row, "unavailabilities")
                flag_modified(row, "wellbeing")


def get_context(authorization: str | None) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    return serialize_context(_state_from_rows(company, fiches))


def patch_context(authorization: str | None, body: dict[str, Any]) -> dict[str, Any]:
    require_database()
    if not isinstance(body, dict):
        raise _invalid()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    state = _state_from_rows(company, fiches)
    try:
        _apply_patch(state, company, body)
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError):
        raise _invalid() from None
    _persist_state(restaurant_id, state)
    company, fiches = _load_company(restaurant_id)
    return serialize_context(_state_from_rows(company, fiches))


def seed_example(authorization: str | None) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    state = _state_from_rows(company, fiches)
    try:
        seed_example_context(state)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise _invalid() from exc
    state.identity = replace(state.identity, linked_employee_ids=frozenset())
    _persist_state(restaurant_id, state, smash_live=True)
    company, fiches = _load_company(restaurant_id)
    return serialize_context(_state_from_rows(company, fiches))


def export_context(authorization: str | None) -> dict[str, Any]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    return serialize_export(_state_from_rows(company, fiches))


def import_context(authorization: str | None, body: dict[str, Any]) -> dict[str, Any]:
    require_database()
    if not isinstance(body, dict):
        raise _invalid()
    version = body.get("export_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise _invalid()
    if any(key not in body for key in EXPORT_SECTIONS):
        raise _invalid()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    current = _state_from_rows(company, fiches)
    state = empty_restaurant(restaurant_id)
    state.identity = replace(current.identity, linked_employee_ids=frozenset())
    patch = {key: body[key] for key in EXPORT_SECTIONS}
    company.linked_employee_ids = []
    try:
        _apply_patch(state, company, patch)
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError):
        raise _invalid() from None
    _persist_state(restaurant_id, state, smash_live=True)
    company, fiches = _load_company(restaurant_id)
    return serialize_context(_state_from_rows(company, fiches))


def _apply_patch(state: RestaurantState, company: Company, body: dict[str, Any]) -> None:
    if FORBIDDEN_PATCH & body.keys():
        raise _invalid()
    if "name" in body:
        if not isinstance(body["name"], str):
            raise ValueError("invalid name")
        set_restaurant_name(state, body["name"])
    if "services" in body:
        services = body["services"]
        if not isinstance(services, list) or len(services) != len(set(services)):
            raise ValueError("invalid services")
        if any(item not in SERVICE_IDS for item in services):
            raise ValueError("invalid services")
        set_services(state, services)
    if "ladders" in body:
        ladders = body["ladders"]
        if not isinstance(ladders, dict):
            raise ValueError("invalid ladders")
        state.ladders = {}
        for team in TEAMS:
            payload = ladders.get(team.value)
            if payload is None:
                continue
            set_role_ladder(state, _ladder_from_json(team, payload))
    if "types" in body:
        types = body["types"]
        if not isinstance(types, list):
            raise ValueError("invalid types")
        state.service_types = []
        for item in types:
            upsert_service_type(state, _type_from_json(item))
    if "typical_week" in body:
        week = _week_from_json(body["typical_week"])
        state.typical_week = None
        if week is not None:
            set_typical_week(state, week)
    if "employees" in body:
        _replace_employees(state, company, body["employees"])


def _replace_employees(state: RestaurantState, company: Company, items: Any) -> None:
    if not isinstance(items, list):
        raise ValueError("invalid employees")
    new_ids = []
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise ValueError("invalid employee")
        new_ids.append(str(item["id"]))
    if len(new_ids) != len(set(new_ids)):
        raise ValueError("duplicate employee id")
    linked = set(company.linked_employee_ids or [])
    missing_linked = linked - set(new_ids)
    if missing_linked:
        raise HTTPException(status_code=409, detail=DETAIL_FICHE_LINKED)
    existing = {person.id: person for person in state.employees}
    state.employees = []
    for item in items:
        current_id = str(item["id"])
        previous = existing.get(current_id)
        token = previous.invite_token if previous is not None else None
        upsert_employee(state, _employee_from_json(item, token))
