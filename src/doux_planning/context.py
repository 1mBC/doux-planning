from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from doux_planning.invites import RestaurantIdentity
from doux_planning.planning import RestaurantState
from doux_planning.staff import Employee, RoleLadder
from doux_planning.structures import (
    RestaurantHours,
    ServiceStructure,
    ServiceType,
    TypicalWeek,
)
from doux_planning.types import ServiceName, Team, WEEKDAYS

COMPANY_SERVICE_IDS = frozenset(
    {ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value}
)


def empty_restaurant(restaurant_id: str) -> RestaurantState:
    return RestaurantState(
        identity=RestaurantIdentity(id=restaurant_id, name="", legal_context_id="france"),
        employees=[],
        structures=[],
        hours=None,
        cycle=None,
    )


def set_restaurant_name(state: RestaurantState, name: str) -> RestaurantState:
    state.identity = replace(state.identity, name=name)
    return state


def set_role_ladder(state: RestaurantState, ladder: RoleLadder) -> RestaurantState:
    state.ladders[ladder.team] = ladder
    return state


def set_services(state: RestaurantState, service_ids: Sequence[str]) -> RestaurantState:
    chosen: list[str] = []
    for service_id in service_ids:
        if service_id not in COMPANY_SERVICE_IDS:
            raise ValueError(f"Unknown company service: {service_id}")
        if service_id not in chosen:
            chosen.append(service_id)
    state.company_services = tuple(chosen)
    state.hours = RestaurantHours.multi_service(*chosen) if chosen else None
    return state


def upsert_service_type(state: RestaurantState, service_type: ServiceType) -> RestaurantState:
    state.service_types = [item for item in state.service_types if item.id != service_type.id] + [service_type]
    return state


def set_typical_week(state: RestaurantState, week: TypicalWeek) -> RestaurantState:
    state.typical_week = week
    return state


def upsert_employee(state: RestaurantState, employee: Employee) -> RestaurantState:
    state.employees = [item for item in state.employees if item.id != employee.id] + [employee]
    return state


def expand_typical_week(state: RestaurantState) -> list[ServiceStructure]:
    if state.typical_week is None:
        return []
    types = {item.id: item for item in state.service_types}
    groups: dict[tuple[str, Team, str], list[str]] = {}
    for cell in state.typical_week.cells:
        if cell.closed or not cell.type_id:
            continue
        kind = types.get(cell.type_id)
        if kind is None or kind.team != cell.team or kind.service_id != cell.service_id:
            continue
        key = (kind.id, kind.team, kind.service_id)
        groups.setdefault(key, []).append(cell.weekday)
    return [
        ServiceStructure(
            id=type_id,
            team=team,
            service_id=service_id,
            weekdays=frozenset(weekdays),
            arrivals=types[type_id].arrivals,
            departures=types[type_id].departures,
        )
        for (type_id, team, service_id), weekdays in groups.items()
    ]


def team_ready(state: RestaurantState, team: Team) -> bool:
    if state.ladders.get(team) is None:
        return False
    if not any(person.team == team for person in state.employees):
        return False
    if not state.company_services:
        return False
    if state.typical_week is None:
        return False
    open_cells = [cell for cell in state.typical_week.cells if cell.team == team and not cell.closed]
    if not open_cells:
        return False
    types = [item for item in state.service_types if item.team == team]
    by_id = {item.id: item for item in types}
    for service_id in {cell.service_id for cell in open_cells}:
        if not any(item.service_id == service_id for item in types):
            return False
    for cell in open_cells:
        kind = by_id.get(cell.type_id or "")
        if kind is None or kind.service_id != cell.service_id:
            return False
    return True


def fortnight_coverage(structures: Sequence[ServiceStructure]) -> tuple[tuple, tuple]:
    def week_key(week_start: int) -> tuple:
        return tuple(
            sorted(
                (item.team.value, item.service_id, item.arrivals, item.departures, WEEKDAYS[day % 7])
                for day in range(week_start, week_start + 7)
                for item in structures
                if item.applies_to(WEEKDAYS[day % 7])
            )
        )

    return week_key(0), week_key(7)
