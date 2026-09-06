from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace

from doux_planning.engine import (
    PlanningDraft,
    Shift,
    _adjacent_rest_pairs,
    _below_role_count,
    _closed_days,
    _coupure_count_in_week,
    _service_count,
    evaluate,
    generate_cycle,
)
from doux_planning.hydrate import _employee, _hours, _structure, data_dir
from doux_planning.invites import RestaurantIdentity, UnknownEmployee
from doux_planning.planning import CONTRACT_HOUR_TOLERANCE, PublishedCycle, RestaurantState, Sandbox
from doux_planning.staff import Employee, Role, RoleLadder, Unavailability, default_legal_rules
from doux_planning.structures import (
    RestaurantHours,
    ServiceStructure,
    ServiceType,
    TypicalWeek,
    TypicalWeekCell,
)
from doux_planning.types import (
    SERVICE_FR,
    WEEKDAY_FR,
    WEEKDAYS,
    SearchEffort,
    ServiceName,
    Team,
    WarningSeverity,
    WeekendChoice,
    week_label_for_day,
    week_label_scheme_from_weekends,
)

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


SERVICE_WISH_CODES = {
    ServiceName.MORNING.value: "max_mornings",
    ServiceName.MIDDAY.value: "max_middays",
    ServiceName.EVENING.value: "max_evenings",
}
WEEKEND_WISH_CODES = {
    WeekendChoice.EVERY_TWO: "weekend_every_two_weeks",
    WeekendChoice.EVEN: "weekend_even_weeks",
    WeekendChoice.ODD: "weekend_odd_weeks",
}


@dataclass(frozen=True)
class BoardContract:
    weekly: float
    assigned: float
    ok: bool


@dataclass(frozen=True)
class BoardWish:
    kind: str
    held: bool
    value: str | None = None
    service_id: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class EmployeeBoard:
    employee_id: str
    team: Team
    assignments: tuple[Shift, ...]
    contract: BoardContract
    wishes: tuple[BoardWish, ...]
    unavailabilities: tuple[Unavailability, ...]


@dataclass(frozen=True)
class RecapHours:
    assigned: float
    contracted: float
    percent: int


@dataclass(frozen=True)
class RecapWellbeing:
    held: int
    total: int


@dataclass(frozen=True)
class RecapStats:
    assignments: int
    empty: int
    interdit: int
    below_role: int
    hours: RecapHours
    wellbeing: RecapWellbeing


@dataclass(frozen=True)
class RecapCell:
    ok: bool
    text: str


@dataclass(frozen=True)
class LegalCol:
    id: str
    label_fr: str


@dataclass(frozen=True)
class WishCol:
    key: str
    label: str


@dataclass(frozen=True)
class RecapRow:
    name: str
    employee_id: str
    cells: dict[str, RecapCell | None]


@dataclass(frozen=True)
class CycleRecap:
    stats: RecapStats
    legal_cols: tuple[LegalCol, ...]
    legal_rows: tuple[RecapRow, ...]
    wish_cols: tuple[WishCol, ...]
    wish_rows: tuple[RecapRow, ...]


def empty_restaurant(restaurant_id: str) -> RestaurantState:
    return RestaurantState(
        identity=RestaurantIdentity(id=restaurant_id, name="", legal_context_id="france"),
        employees=[],
        structures=[],
        hours=None,
        cycle=None,
    )


def seed_example_context(state: RestaurantState) -> RestaurantState:
    path = data_dir() / "examples" / "saint-cloud.json"
    restaurant = json.loads(path.read_text(encoding="utf-8"))["restaurant"]
    hours = _hours(restaurant["hours"])
    example_structures = [_structure(item) for item in restaurant["structures"]]
    employees = [_employee(item) for item in restaurant["employees"]]

    state.hours = hours
    state.company_services = tuple(hours.services)
    state.service_types = [
        ServiceType(
            id=item.id,
            name=item.id,
            team=item.team,
            service_id=item.service_id,
            arrivals=item.arrivals,
            departures=item.departures,
        )
        for item in example_structures
    ]

    cells: list[TypicalWeekCell] = []
    for team in Team:
        for service_id in state.company_services:
            for weekday in WEEKDAYS:
                match = next(
                    (
                        item
                        for item in example_structures
                        if item.team == team and item.service_id == service_id and weekday in item.weekdays
                    ),
                    None,
                )
                cells.append(
                    TypicalWeekCell(
                        weekday=weekday,
                        service_id=service_id,
                        type_id=None if match is None else match.id,
                        closed=match is None,
                        team=team,
                    )
                )
    state.typical_week = TypicalWeek(cells=tuple(cells))

    unique_roles: dict[tuple[str, int, Team], Role] = {}
    for person in employees:
        role = person.role
        unique_roles.setdefault((role.name, role.level, role.team), role)
    state.ladders = {}
    for team in {role.team for role in unique_roles.values()}:
        state.ladders[team] = RoleLadder(
            team,
            tuple(role for role in unique_roles.values() if role.team == team),
            substitution_explained=True,
        )

    state.employees = employees
    state.structures = expand_typical_week(state)
    state.published_cycles = {Team.SALLE: None, Team.CUISINE: None}
    state.live_sandboxes = {Team.SALLE: None, Team.CUISINE: None}
    state.cycle = None
    state.accounts = []
    return state


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
    wishes = _board_wishes(person, warnings)
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


def week_label_scheme(state: RestaurantState) -> str:
    return week_label_scheme_from_weekends(person.wellbeing.weekend for person in state.employees)


WISH_COL_LABELS = {
    "contrat": "Contrat",
    "indispo": "Indispos",
    "consecutive_rest": "Deux repos consécutifs par semaine",
    "weekend_rest_day": "Au moins un repos samedi ou dimanche",
    "weekend": "Week-end",
    "max_morning": "Max petit-déj",
    "max_midday": "Max déj",
    "max_evening": "Max dîner",
    "max_coupures": "Nbre de coupures max",
}
WEEKEND_FR = {
    WeekendChoice.EVERY_TWO: "un week-end sur deux",
    WeekendChoice.EVEN: "paire",
    WeekendChoice.ODD: "impaire",
}
MAX_DAILY_RULE = {Team.SALLE: "max_daily_salle", Team.CUISINE: "max_daily_cuisine"}


def cycle_recap(state: RestaurantState, team: Team) -> CycleRecap:
    published = state.published_cycles.get(team)
    if published is None:
        raise NoPublishedCycle(team)
    staff = [person for person in state.employees if person.team == team]
    result = published.result
    draft = published.draft
    warnings = result.warnings
    assignments = result.assignments
    assigned = sum(shift.duration_hours for shift in assignments)
    contracted = sum(person.contractual_hours_per_week for person in staff) * 2
    percent = 0 if contracted == 0 else round(100 * assigned / contracted)
    wish_lists = [_board_wishes(person, warnings) for person in staff]
    posed = [wish for row in wish_lists for wish in row]
    legal_rows = tuple(_legal_row(person, assignments, warnings) for person in staff)
    used_rules = {rule_id for row in legal_rows for rule_id in row.cells}
    legal_cols = tuple(
        LegalCol(id=rule.id, label_fr=rule.label_fr)
        for rule in default_legal_rules()
        if rule.id in used_rules
    )
    wish_keys = _wish_col_keys(staff)
    wish_cols = tuple(WishCol(key=key, label=WISH_COL_LABELS[key]) for key in wish_keys)
    scheme = week_label_scheme_from_weekends(person.wellbeing.weekend for person in draft.employees)
    wish_rows = tuple(
        _wish_row(person, wishes, assignments, warnings, wish_keys, draft.hours, scheme)
        for person, wishes in zip(staff, wish_lists)
    )
    return CycleRecap(
        stats=RecapStats(
            assignments=len(assignments),
            empty=sum(1 for item in warnings if item.code == "empty_post"),
            interdit=sum(1 for item in warnings if item.severity == WarningSeverity.INTERDIT),
            below_role=_below_role_count(draft, assignments),
            hours=RecapHours(assigned=assigned, contracted=contracted, percent=percent),
            wellbeing=RecapWellbeing(
                held=sum(1 for wish in posed if wish.held),
                total=len(posed),
            ),
        ),
        legal_cols=legal_cols,
        legal_rows=legal_rows,
        wish_cols=wish_cols,
        wish_rows=wish_rows,
    )


def _hours_label(value: float) -> str:
    minutes = int(round(value * 60))
    hours, mins = divmod(minutes, 60)
    if mins == 0:
        return f"{hours}h"
    if mins == 30:
        return f"{hours}h30"
    return f"{hours}h{mins:02d}"


def _has_interdit(warnings, employee_id: str, code: str) -> bool:
    return any(
        item.severity == WarningSeverity.INTERDIT and item.employee_id == employee_id and item.code == code
        for item in warnings
    )


def _has_code(warnings, employee_id: str, code: str) -> bool:
    return any(item.employee_id == employee_id and item.code == code for item in warnings)


def _shifts_by_day(assignments, employee_id: str) -> dict[int, list[Shift]]:
    by_day: dict[int, list[Shift]] = {}
    for shift in assignments:
        if shift.employee_id == employee_id:
            by_day.setdefault(shift.day_index, []).append(shift)
    return by_day


def _week_hours(by_day: dict[int, list[Shift]], week_start: int) -> float:
    return sum(
        item.duration_hours
        for day in range(week_start, week_start + 7)
        for item in by_day.get(day, [])
    )


def _rest_days(by_day: dict[int, list[Shift]], week_start: int) -> int:
    return sum(1 for day in range(week_start, week_start + 7) if day not in by_day)


def _max_coupure_hours(by_day: dict[int, list[Shift]]) -> float:
    longest = 0.0
    for day_shifts in by_day.values():
        ordered = sorted(day_shifts, key=lambda item: item.start_minutes)
        for first, second in zip(ordered, ordered[1:]):
            longest = max(longest, (second.start_minutes - first.end_minutes) / 60)
    return longest


def _max_daily_hours(by_day: dict[int, list[Shift]]) -> float:
    if not by_day:
        return 0.0
    return max(sum(item.duration_hours for item in day_shifts) for day_shifts in by_day.values())


def _rest_between_clocks(warnings, employee_id: str) -> str:
    for item in warnings:
        if item.code == "rest_between_days" and item.employee_id == employee_id:
            start = item.message.find("(")
            end = item.message.rfind(")")
            if start != -1 and end > start:
                return item.message[start + 1 : end]
    return ""


def _legal_row(person, assignments, warnings) -> RecapRow:
    by_day = _shifts_by_day(assignments, person.id)
    rest_a, rest_b = _rest_days(by_day, 0), _rest_days(by_day, 7)
    tightest = min(rest_a, rest_b)
    rest_ok = not _has_interdit(warnings, person.id, "weekly_rest_days")
    coupure = _max_coupure_hours(by_day)
    coupure_ok = not _has_interdit(warnings, person.id, "max_coupure")
    daily = _max_daily_hours(by_day)
    daily_ok = not _has_interdit(warnings, person.id, "max_daily_hours")
    week_a, week_b = _week_hours(by_day, 0), _week_hours(by_day, 7)
    weekly_ok = not _has_interdit(warnings, person.id, "max_weekly_hours")
    rest_between_ok = not _has_code(warnings, person.id, "rest_between_days")
    daily_rule = MAX_DAILY_RULE[person.team]
    cells: dict[str, RecapCell | None] = {
        "rest_between_days": RecapCell(
            ok=rest_between_ok,
            text="OK · min 11h" if rest_between_ok else _rest_between_clocks(warnings, person.id),
        ),
        "weekly_rest_days": RecapCell(
            ok=rest_ok,
            text=f"{'OK · ' if rest_ok else ''}{tightest} / 2 j.",
        ),
        "max_coupure": RecapCell(
            ok=coupure_ok,
            text=f"{'OK · ' if coupure_ok else ''}max {_hours_label(coupure)}",
        ),
        daily_rule: RecapCell(
            ok=daily_ok,
            text=f"{'OK · ' if daily_ok else ''}max {_hours_label(daily)}",
        ),
        "max_weekly_hours": RecapCell(
            ok=weekly_ok,
            text=f"{'OK · ' if weekly_ok else ''}{_hours_label(week_a)} / {_hours_label(week_b)}",
        ),
    }
    return RecapRow(name=person.name, employee_id=person.id, cells=cells)


def _wish_col_keys(staff) -> list[str]:
    keys = ["contrat"]
    if any(person.unavailabilities for person in staff):
        keys.append("indispo")
    if any(person.wellbeing.consecutive_rest for person in staff):
        keys.append("consecutive_rest")
    if any(person.wellbeing.weekend_rest_day for person in staff):
        keys.append("weekend_rest_day")
    if any(person.wellbeing.weekend is not None for person in staff):
        keys.append("weekend")
    if any(ServiceName.MORNING.value in person.wellbeing.max_services for person in staff):
        keys.append("max_morning")
    if any(ServiceName.MIDDAY.value in person.wellbeing.max_services for person in staff):
        keys.append("max_midday")
    if any(ServiceName.EVENING.value in person.wellbeing.max_services for person in staff):
        keys.append("max_evening")
    if any(person.wellbeing.max_coupures_per_week is not None for person in staff):
        keys.append("max_coupures")
    return keys


def _wish_text(ok: bool, extra: str | None = None) -> str:
    base = "OK" if ok else "Non tenu"
    return f"{base} · {extra}" if extra else base


def _max_measure(limit: int, count_a: int, count_b: int, held: bool) -> str:
    measure = f"max {limit} · {count_a} / {count_b} posés"
    return f"OK · {measure}" if held else measure


def _first_warning_week(warnings, employee_id: str, code: str, scheme: str) -> str:
    for item in warnings:
        if item.employee_id == employee_id and item.code == code and item.day_index is not None:
            return week_label_for_day(item.day_index, scheme)
    return week_label_for_day(0, scheme)


def _indispo_text(person, assignments, warnings) -> str:
    ok = not _has_interdit(warnings, person.id, "unavailability")
    if ok:
        return f"OK · {len(person.unavailabilities)} créneaux"
    for shift in sorted(assignments, key=lambda item: (item.day_index, item.start_minutes)):
        if shift.employee_id != person.id:
            continue
        for pattern in person.unavailabilities:
            if pattern.blocks(shift.weekday, shift.service_id):
                service = SERVICE_FR.get(shift.service_id, shift.service_id)
                return f"Non tenu · {WEEKDAY_FR[shift.weekday]} {service}"
    return "Non tenu"


def _adjacent_rest_span(by_day, hours) -> str | None:
    for week_start in (0, 7):
        closed = _closed_days(hours, week_start) if hours is not None else set()
        offs = {day for day in range(week_start, week_start + 7) if day not in by_day} | closed
        for left, right in _adjacent_rest_pairs(week_start):
            if left in offs and right in offs:
                return f"{WEEKDAY_FR[WEEKDAYS[left % 7]]}–{WEEKDAY_FR[WEEKDAYS[right % 7]]}"
    return None


def _weekend_off_short(by_day, hours) -> str:
    for week_start in (0, 7):
        closed = _closed_days(hours, week_start) if hours is not None else set()
        saturday, sunday = week_start + 5, week_start + 6
        sat_off = saturday not in by_day or saturday in closed
        sun_off = sunday not in by_day or sunday in closed
        if sat_off:
            return "sam"
        if sun_off:
            return "dim"
    return "sam"


def _wish_row(person, wishes, assignments, warnings, keys: Sequence[str], hours, scheme: str) -> RecapRow:
    by_kind = {wish.kind: wish for wish in wishes}
    by_service = {wish.service_id: wish for wish in wishes if wish.kind == "max_services"}
    by_day = _shifts_by_day(assignments, person.id)
    week_a, week_b = _week_hours(by_day, 0), _week_hours(by_day, 7)
    contract_ok = not _has_code(warnings, person.id, "contract_hours")
    cells: dict[str, RecapCell | None] = {}
    for key in keys:
        if key == "contrat":
            cells[key] = RecapCell(
                ok=contract_ok,
                text=f"{_hours_label(week_a)} · {_hours_label(week_b)} / {_hours_label(person.contractual_hours_per_week)}",
            )
            continue
        if key == "indispo":
            if not person.unavailabilities:
                cells[key] = None
                continue
            cells[key] = RecapCell(
                ok=not _has_interdit(warnings, person.id, "unavailability"),
                text=_indispo_text(person, assignments, warnings),
            )
            continue
        if key == "max_morning":
            wish = by_service.get(ServiceName.MORNING.value)
        elif key == "max_midday":
            wish = by_service.get(ServiceName.MIDDAY.value)
        elif key == "max_evening":
            wish = by_service.get(ServiceName.EVENING.value)
        else:
            wish = by_kind.get(key)
        if wish is None:
            cells[key] = None
            continue
        if key in {"max_morning", "max_midday", "max_evening"}:
            service_id = wish.service_id or ""
            cells[key] = RecapCell(
                ok=wish.held,
                text=_max_measure(
                    wish.limit or 0,
                    _service_count(by_day, 0, service_id),
                    _service_count(by_day, 7, service_id),
                    wish.held,
                ),
            )
            continue
        if key == "max_coupures":
            cells[key] = RecapCell(
                ok=wish.held,
                text=_max_measure(
                    wish.limit or 0,
                    _coupure_count_in_week(assignments, person.id, 0),
                    _coupure_count_in_week(assignments, person.id, 7),
                    wish.held,
                ),
            )
            continue
        if key == "consecutive_rest":
            if wish.held:
                span = _adjacent_rest_span(by_day, hours)
                extra = f"tenu · {span}" if span else "tenu"
            else:
                extra = f"sem. {_first_warning_week(warnings, person.id, 'consecutive_rest_days', scheme)}"
            cells[key] = RecapCell(ok=wish.held, text=_wish_text(wish.held, extra))
            continue
        if key == "weekend_rest_day":
            if wish.held:
                extra = _weekend_off_short(by_day, hours)
            else:
                extra = f"sem. {_first_warning_week(warnings, person.id, 'weekend_rest_day', scheme)}"
            cells[key] = RecapCell(ok=wish.held, text=_wish_text(wish.held, extra))
            continue
        extra = WEEKEND_FR.get(person.wellbeing.weekend) if key == "weekend" else None
        cells[key] = RecapCell(ok=wish.held, text=_wish_text(wish.held, extra))
    return RecapRow(name=person.name, employee_id=person.id, cells=cells)


def _held(warnings, employee_id: str, code: str) -> bool:
    return not any(
        item.severity == WarningSeverity.SOUHAIT and item.employee_id == employee_id and item.code == code
        for item in warnings
    )


def _board_wishes(person, warnings) -> tuple[BoardWish, ...]:
    wish = person.wellbeing
    rows: list[BoardWish] = []
    if wish.consecutive_rest:
        rows.append(BoardWish(kind="consecutive_rest", held=_held(warnings, person.id, "consecutive_rest_days")))
    if wish.weekend_rest_day:
        rows.append(BoardWish(kind="weekend_rest_day", held=_held(warnings, person.id, "weekend_rest_day")))
    if wish.weekend is not None:
        rows.append(
            BoardWish(
                kind="weekend",
                value=wish.weekend.value,
                held=_held(warnings, person.id, WEEKEND_WISH_CODES[wish.weekend]),
            )
        )
    for service_id in (ServiceName.MORNING.value, ServiceName.MIDDAY.value, ServiceName.EVENING.value):
        if service_id not in wish.max_services:
            continue
        rows.append(
            BoardWish(
                kind="max_services",
                service_id=service_id,
                limit=wish.max_services[service_id],
                held=_held(warnings, person.id, SERVICE_WISH_CODES[service_id]),
            )
        )
    if wish.max_coupures_per_week is not None:
        rows.append(
            BoardWish(
                kind="max_coupures",
                limit=wish.max_coupures_per_week,
                held=_held(warnings, person.id, "max_coupures"),
            )
        )
    return tuple(rows)
