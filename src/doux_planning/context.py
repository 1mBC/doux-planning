from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from doux_planning.engine import PlanningDraft, Shift, evaluate, generate_cycle
from doux_planning.invites import RestaurantIdentity, UnknownEmployee
from doux_planning.planning import CONTRACT_HOUR_TOLERANCE, PublishedCycle, RestaurantState, Sandbox
from doux_planning.staff import Employee, RoleLadder, Unavailability, default_legal_rules
from doux_planning.structures import (
    RestaurantHours,
    ServiceStructure,
    ServiceType,
    TypicalWeek,
)
from doux_planning.types import SearchEffort, ServiceName, Team, WarningSeverity, WEEKDAYS, WellbeingPreference

COMPANY_SERVICE_IDS = frozenset(
    {ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value}
)


class TeamNotReady(ValueError):
    def __init__(self, team: Team) -> None:
        self.team = team
        super().__init__(f"team {team.value} is not ready")


class NoPublishedCycle(ValueError):
    def __init__(self, team: Team) -> None:
        self.team = team
        super().__init__(f"no published cycle for {team.value}")


WISH_WARNING_CODES = {
    WellbeingPreference.TWO_CONSECUTIVE_REST_DAYS: "consecutive_rest_days",
    WellbeingPreference.WEEKEND_OFF_EVERY_TWO_WEEKS: "weekend_every_two_weeks",
    WellbeingPreference.AT_LEAST_ONE_WEEKEND_REST_DAY: "weekend_rest_day",
    WellbeingPreference.NO_EVENING_SERVICE: "no_evening",
    WellbeingPreference.NO_MORNING_SERVICE: "no_morning",
    WellbeingPreference.MAX_TWO_COUPURES_PER_WEEK: "max_coupures",
    WellbeingPreference.MAX_THREE_COUPURES_PER_WEEK: "max_coupures",
}


@dataclass(frozen=True)
class BoardContract:
    weekly: float
    assigned: float
    ok: bool


@dataclass(frozen=True)
class BoardWish:
    key: WellbeingPreference
    held: bool


@dataclass(frozen=True)
class EmployeeBoard:
    employee_id: str
    team: Team
    assignments: tuple[Shift, ...]
    contract: BoardContract
    wishes: tuple[BoardWish, ...]
    unavailabilities: tuple[Unavailability, ...]


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


def generate_team(
    state: RestaurantState,
    team: Team,
    search: SearchEffort = SearchEffort.OPTIMIZED,
) -> RestaurantState:
    if not team_ready(state, team):
        raise TeamNotReady(team)
    structures = tuple(item for item in expand_typical_week(state) if item.team == team)
    employees = tuple(person for person in state.employees if person.team == team)
    draft = PlanningDraft(
        employees=employees,
        structures=structures,
        hours=state.hours,
        legal_rules=default_legal_rules(),
        search_effort=search,
    )
    result = generate_cycle(draft, search)
    published = PublishedCycle(
        id=team.value,
        draft=draft.with_assignments(result.assignments),
        result=result,
    )
    state.published_cycles[team] = published
    return state


def enter_live_sandbox(state: RestaurantState, team: Team) -> Sandbox:
    published = state.published_cycles.get(team)
    if published is None:
        raise NoPublishedCycle(team)
    existing = state.live_sandboxes.get(team)
    if existing is not None:
        return existing
    sandbox = Sandbox(
        restaurant_id=state.identity.id,
        target="cycle",
        week_id=None,
        draft=replace(published.draft),
        last_result=published.result,
    )
    state.live_sandboxes[team] = sandbox
    return sandbox


def discard_live_sandbox(state: RestaurantState, team: Team) -> None:
    state.live_sandboxes[team] = None


def publish_live_sandbox(state: RestaurantState, team: Team) -> RestaurantState:
    sandbox = state.live_sandboxes.get(team)
    if sandbox is None:
        raise RuntimeError("No live sandbox")
    result = sandbox.last_result or evaluate(sandbox.draft)
    published = state.published_cycles.get(team)
    if published is None:
        raise NoPublishedCycle(team)
    state.published_cycles[team] = PublishedCycle(
        id=published.id,
        draft=sandbox.draft.with_assignments(result.assignments),
        result=result,
    )
    state.live_sandboxes[team] = None
    return state


def employee_board(state: RestaurantState, employee_id: str) -> EmployeeBoard:
    person = next((item for item in state.employees if item.id == employee_id), None)
    if person is None:
        raise UnknownEmployee("Unknown employee")
    published = state.published_cycles.get(person.team)
    assignments = published.result.assignments if published is not None else ()
    warnings = published.result.warnings if published is not None else ()
    assigned = round(
        sum(shift.duration_hours for shift in assignments if shift.employee_id == person.id),
        2,
    )
    if published is None:
        ok = abs(assigned - person.contractual_hours_per_week) <= CONTRACT_HOUR_TOLERANCE
    else:
        ok = not any(item.code == "contract_hours" and item.employee_id == person.id for item in warnings)
    wishes = tuple(
        BoardWish(
            key=pref,
            held=not any(
                item.severity == WarningSeverity.SOUHAIT
                and item.employee_id == person.id
                and item.code == WISH_WARNING_CODES[pref]
                for item in warnings
            ),
        )
        for pref in sorted(person.wellbeing, key=lambda item: item.value)
    )
    return EmployeeBoard(
        employee_id=person.id,
        team=person.team,
        assignments=assignments,
        contract=BoardContract(
            weekly=person.contractual_hours_per_week,
            assigned=assigned,
            ok=ok,
        ),
        wishes=wishes,
        unavailabilities=person.unavailabilities,
    )
