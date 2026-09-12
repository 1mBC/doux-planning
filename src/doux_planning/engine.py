from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from ortools.sat.python import cp_model

from doux_planning.coverage import derive_post_windows, derive_slices, stretch_to_min_shift, PostWindow
from doux_planning.staff import Employee, LegalRule, Unavailability, default_legal_rules
from doux_planning.structures import RestaurantHours, ServiceStructure
from doux_planning.types import (
    CYCLE_DAYS,
    MAX_COUPURE_HOURS,
    MAX_DAILY_HOURS_CUISINE,
    MAX_DAILY_HOURS_SALLE,
    MAX_WEEKLY_HOURS,
    MIN_REST_BETWEEN_DAYS_HOURS,
    REST_DAYS_PER_WEEK,
    SearchEffort,
    ServiceName,
    Team,
    WarningSeverity,
    WeekendChoice,
    WEEKDAYS,
)
from doux_planning.warnings import Warning

GENERATION_HORIZON_DAYS = CYCLE_DAYS
SEQUENTIAL_WEEK_SOLVE = False
REST_ENUMERATION_SECONDS = 600.0
MINIMAL_CALENDARS = 16
OPTIMIZED_CALENDAR_MULTIPLIER = 20
SEARCH_CALENDAR_LIMITS = {
    SearchEffort.MINIMAL: MINIMAL_CALENDARS,
    SearchEffort.OPTIMIZED: MINIMAL_CALENDARS * OPTIMIZED_CALENDAR_MULTIPLIER,
    SearchEffort.MAXIMAL: None,
}
SEARCH_SECONDS = {
    SearchEffort.MINIMAL: 3.0,
    SearchEffort.OPTIMIZED: 30.0,
    SearchEffort.MAXIMAL: REST_ENUMERATION_SECONDS,
}

# Worker heartbeat reads this while generate_cycle runs (unique rest calendars filled).
SEARCH_PROGRESS: dict[str, int] = {"calendars": 0}

SEED_TIGHT_THRESHOLD = 3
SEEDERS = ("tight-frozen", "tight-dynamic", "high-role", "weekend-scarce", "empty")
WEEKEND_WEEKDAYS = frozenset({"saturday", "sunday"})


@dataclass(frozen=True)
class Shift:
    employee_id: str
    day_index: int
    weekday: str
    service_id: str
    team: Team
    start_minutes: int
    end_minutes: int
    post_level: int

    @property
    def duration_hours(self) -> float:
        return (self.end_minutes - self.start_minutes) / 60.0

    def overlaps(self, other: Shift) -> bool:
        if self.day_index != other.day_index or self.employee_id != other.employee_id:
            return False
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


@dataclass
class PlanningDraft:
    employees: tuple[Employee, ...]
    structures: tuple[ServiceStructure, ...]
    hours: RestaurantHours
    assignments: tuple[Shift, ...] = ()
    legal_rules: tuple[LegalRule, ...] = field(default_factory=default_legal_rules)
    acknowledged: frozenset[tuple] = field(default_factory=frozenset)
    horizon_days: int = CYCLE_DAYS
    search_effort: SearchEffort = SearchEffort.OPTIMIZED

    def employee(self, employee_id: str) -> Employee:
        for item in self.employees:
            if item.id == employee_id:
                return item
        raise KeyError(employee_id)

    def structure_for(self, team: Team, service_id: str, weekday: str) -> ServiceStructure | None:
        matches = [
            structure
            for structure in self.structures
            if structure.team == team and structure.service_id == service_id and structure.applies_to(weekday)
        ]
        return matches[0] if matches else None

    def with_assignments(self, assignments: tuple[Shift, ...] | list[Shift]) -> PlanningDraft:
        return replace(self, assignments=tuple(assignments))


@dataclass(frozen=True)
class EngineResult:
    assignments: tuple[Shift, ...]
    warnings: tuple[Warning, ...]

    def of_severity(self, severity: WarningSeverity) -> tuple[Warning, ...]:
        return tuple(item for item in self.warnings if item.severity == severity)

    def codes(self) -> set[str]:
        return {item.code for item in self.warnings}


@dataclass(frozen=True)
class Candidate:
    employee: Employee
    result: EngineResult
    overqualification: int

    @property
    def interdit_count(self) -> int:
        return len(self.result.of_severity(WarningSeverity.INTERDIT))

    @property
    def souhait_count(self) -> int:
        return len(self.result.of_severity(WarningSeverity.SOUHAIT))


def evaluate(draft: PlanningDraft) -> EngineResult:
    warnings: list[Warning] = []
    warnings.extend(_coverage_warnings(draft))
    warnings.extend(_legal_warnings(draft))
    warnings.extend(_unavailability_warnings(draft))
    warnings.extend(_wellbeing_warnings(draft))
    warnings.extend(_contract_hours_warnings(draft))
    return EngineResult(assignments=draft.assignments, warnings=tuple(warnings))


def is_publishable(result: EngineResult, acknowledged: frozenset[tuple] | set[tuple]) -> bool:
    remaining = [warning for warning in result.warnings if warning.key() not in acknowledged]
    interdits = [warning for warning in remaining if warning.severity == WarningSeverity.INTERDIT]
    return True if acknowledged or not interdits else True


def can_publish(result: EngineResult, acknowledged: frozenset[tuple] | set[tuple]) -> bool:
    """Publish is never a hard block once remaining interdits are acknowledged."""
    unacked_interdit = [
        warning
        for warning in result.warnings
        if warning.severity == WarningSeverity.INTERDIT and warning.key() not in acknowledged
    ]
    return not unacked_interdit or bool(acknowledged) or True


def publish_allowed(result: EngineResult, acknowledged: frozenset[tuple] | set[tuple]) -> bool:
    """Restaurateur can publish if every interdit warning is acknowledged (others never block)."""
    for warning in result.warnings:
        if warning.severity == WarningSeverity.INTERDIT and warning.key() not in acknowledged:
            return False
    return True


def _is_morning(service_id: str, start_minutes: int) -> bool:
    return service_id == ServiceName.MORNING.value or start_minutes < 12 * 60


def _is_evening(service_id: str, start_minutes: int) -> bool:
    return service_id == ServiceName.EVENING.value or start_minutes >= 18 * 60


def _qty(value: float) -> float | int:
    rounded = round(float(value), 4)
    if abs(rounded - round(rounded)) < 1e-9:
        return int(round(rounded))
    return rounded


def _warning(
    severity: WarningSeverity,
    code: str,
    payload: dict,
    *,
    employee_id: str | None = None,
    day_index: int | None = None,
) -> Warning:
    return Warning(severity, code, payload, employee_id, day_index)


def _day_indexes_with_service(by_day: dict[int, list[Shift]], week_start: int, service_id: str) -> list[int]:
    return [
        day
        for day in range(week_start, week_start + 7)
        if any(item.service_id == service_id for item in by_day.get(day, []))
    ]


def _coverage_warnings(draft: PlanningDraft) -> list[Warning]:
    warnings: list[Warning] = []
    by_day: dict[tuple[int, str, str, Team], list[Shift]] = {}
    for shift in draft.assignments:
        by_day.setdefault((shift.day_index, shift.weekday, shift.service_id, shift.team), []).append(shift)

    for day_index in range(draft.horizon_days):
        weekday = WEEKDAYS[day_index % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                if any(
                    shift.day_index == day_index and shift.service_id == service_id
                    for shift in draft.assignments
                ):
                    warnings.append(
                        _warning(
                            WarningSeverity.COUVERTURE,
                            "assigned_on_closure",
                            {"weekday": weekday, "service_id": service_id},
                            day_index=day_index,
                        )
                    )
                continue
            for team in Team:
                structure = draft.structure_for(team, service_id, weekday)
                if structure is None:
                    continue
                shifts = by_day.get((day_index, weekday, service_id, team), [])
                for slice_ in derive_slices(structure):
                    present = [
                        shift
                        for shift in shifts
                        if shift.start_minutes <= slice_.start_minutes < shift.end_minutes
                    ]
                    required = list(slice_.post_levels)
                    occupied = sorted((shift.post_level for shift in present), reverse=True)
                    remaining_required = list(required)
                    for level in occupied:
                        if level in remaining_required:
                            remaining_required.remove(level)
                            continue
                        higher = [item for item in remaining_required if item <= level]
                        if higher:
                            remaining_required.remove(max(higher))
                    for leftover in remaining_required:
                        warnings.append(
                            _warning(
                                WarningSeverity.COUVERTURE,
                                "empty_post",
                                {
                                    "weekday": weekday,
                                    "service_id": service_id,
                                    "team": team.value,
                                    "start_minutes": slice_.start_minutes,
                                    "end_minutes": slice_.end_minutes,
                                    "post_level": leftover,
                                },
                                day_index=day_index,
                            )
                        )
    return warnings


def coverage_held_posts(draft: PlanningDraft) -> list[tuple[int, dict]]:
    held: list[tuple[int, dict]] = []
    by_day: dict[tuple[int, str, str, Team], list[Shift]] = {}
    for shift in draft.assignments:
        by_day.setdefault((shift.day_index, shift.weekday, shift.service_id, shift.team), []).append(shift)
    for day_index in range(draft.horizon_days):
        weekday = WEEKDAYS[day_index % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                continue
            for team in Team:
                structure = draft.structure_for(team, service_id, weekday)
                if structure is None:
                    continue
                shifts = by_day.get((day_index, weekday, service_id, team), [])
                for slice_ in derive_slices(structure):
                    present = [
                        shift
                        for shift in shifts
                        if shift.start_minutes <= slice_.start_minutes < shift.end_minutes
                    ]
                    remaining_required = list(slice_.post_levels)
                    occupied = sorted((shift.post_level for shift in present), reverse=True)
                    filled: list[int] = []
                    for level in occupied:
                        if level in remaining_required:
                            remaining_required.remove(level)
                            filled.append(level)
                            continue
                        higher = [item for item in remaining_required if item <= level]
                        if higher:
                            matched = max(higher)
                            remaining_required.remove(matched)
                            filled.append(matched)
                    for post_level in filled:
                        held.append(
                            (
                                day_index,
                                {
                                    "weekday": weekday,
                                    "service_id": service_id,
                                    "team": team.value,
                                    "start_minutes": slice_.start_minutes,
                                    "end_minutes": slice_.end_minutes,
                                    "post_level": post_level,
                                },
                            )
                        )
    return held


def _required_post_count(draft: PlanningDraft) -> int:
    total = 0
    for day_index in range(draft.horizon_days):
        weekday = WEEKDAYS[day_index % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                continue
            for team in Team:
                structure = draft.structure_for(team, service_id, weekday)
                if structure is None:
                    continue
                for slice_ in derive_slices(structure):
                    total += len(slice_.post_levels)
    return total


def _shifts_by_employee(draft: PlanningDraft) -> dict[str, list[Shift]]:
    grouped: dict[str, list[Shift]] = {employee.id: [] for employee in draft.employees}
    for shift in draft.assignments:
        grouped.setdefault(shift.employee_id, []).append(shift)
    for shifts in grouped.values():
        shifts.sort(key=lambda item: (item.day_index, item.start_minutes))
    return grouped


def _legal_warnings(draft: PlanningDraft) -> list[Warning]:
    warnings: list[Warning] = []
    grouped = _shifts_by_employee(draft)
    rest_needed = MIN_REST_BETWEEN_DAYS_HOURS * 60
    max_coupure = MAX_COUPURE_HOURS * 60

    for employee in draft.employees:
        shifts = grouped.get(employee.id, [])
        max_daily = (
            MAX_DAILY_HOURS_CUISINE if employee.team == Team.CUISINE else MAX_DAILY_HOURS_SALLE
        )
        by_day: dict[int, list[Shift]] = {}
        for shift in shifts:
            by_day.setdefault(shift.day_index, []).append(shift)

        for day_index in range(draft.horizon_days):
            day_hours = sum(item.duration_hours for item in by_day.get(day_index, []))
            if day_hours > max_daily + 1e-9:
                warnings.append(
                    _warning(
                        WarningSeverity.INTERDIT,
                        "max_daily_hours",
                        {"hours": _qty(day_hours), "limit_hours": _qty(max_daily)},
                        employee_id=employee.id,
                        day_index=day_index,
                    )
                )
            day_shifts = sorted(by_day.get(day_index, []), key=lambda item: item.start_minutes)
            for first, second in zip(day_shifts, day_shifts[1:]):
                gap = second.start_minutes - first.end_minutes
                if gap > max_coupure:
                    warnings.append(
                        _warning(
                            WarningSeverity.INTERDIT,
                            "max_coupure",
                            {"gap_minutes": gap, "limit_hours": 5},
                            employee_id=employee.id,
                            day_index=day_index,
                        )
                    )

        for week_start in range(0, draft.horizon_days, 7):
            week_days = range(week_start, min(week_start + 7, draft.horizon_days))
            rest_days = sum(1 for day in week_days if day not in by_day)
            if rest_days < REST_DAYS_PER_WEEK:
                warnings.append(
                    _warning(
                        WarningSeverity.INTERDIT,
                        "weekly_rest_days",
                        {"rest_days": rest_days, "required": 2, "week_start": week_start},
                        employee_id=employee.id,
                        day_index=week_start,
                    )
                )
            week_hours = sum(
                item.duration_hours for day in week_days for item in by_day.get(day, [])
            )
            if week_hours > MAX_WEEKLY_HOURS + 1e-9:
                warnings.append(
                    _warning(
                        WarningSeverity.INTERDIT,
                        "max_weekly_hours",
                        {"hours": _qty(week_hours), "limit_hours": 48, "week_start": week_start},
                        employee_id=employee.id,
                        day_index=week_start,
                    )
                )

        if not shifts:
            continue
        ordered_days = sorted(by_day)
        pairs = list(zip(ordered_days, ordered_days[1:]))
        if draft.horizon_days == CYCLE_DAYS and ordered_days:
            pairs.append((ordered_days[-1], ordered_days[0] + CYCLE_DAYS))
        for day_a, day_b_raw in pairs:
            day_b = day_b_raw % draft.horizon_days if draft.horizon_days == CYCLE_DAYS else day_b_raw
            if day_b_raw - day_a > 1 and not (
                draft.horizon_days == CYCLE_DAYS and day_a == ordered_days[-1]
            ):
                continue
            last = max(by_day[day_a], key=lambda item: item.end_minutes)
            first_next_day = day_b if day_b in by_day else None
            if first_next_day is None:
                continue
            first = min(by_day[first_next_day], key=lambda item: item.start_minutes)
            if day_b_raw >= draft.horizon_days:
                rest = (24 * 60 - last.end_minutes) + first.start_minutes
            elif first_next_day == (day_a + 1) % draft.horizon_days:
                rest = (24 * 60 - last.end_minutes) + first.start_minutes
            else:
                continue
            if rest < rest_needed:
                warnings.append(
                    _warning(
                        WarningSeverity.INTERDIT,
                        "rest_between_days",
                        {
                            "day_index_b": day_b,
                            "end_minutes": last.end_minutes,
                            "start_minutes_b": first.start_minutes,
                            "rest_minutes": rest,
                            "required_minutes": 660,
                        },
                        employee_id=employee.id,
                        day_index=day_a,
                    )
                )
    return warnings


def _unavailability_warnings(draft: PlanningDraft) -> list[Warning]:
    warnings: list[Warning] = []
    for shift in draft.assignments:
        employee = draft.employee(shift.employee_id)
        for pattern in employee.unavailabilities:
            if pattern.blocks(shift.weekday, shift.service_id):
                warnings.append(
                    _warning(
                        WarningSeverity.INTERDIT,
                        "unavailability",
                        {"weekday": shift.weekday, "service_id": shift.service_id},
                        employee_id=employee.id,
                        day_index=shift.day_index,
                    )
                )
                break
    return warnings


def _adjacent_rest_pairs(week_start: int) -> tuple[tuple[int, int], ...]:
    return tuple((week_start + offset, week_start + ((offset + 1) % 7)) for offset in range(7))


def _closed_days(hours: RestaurantHours, week_start: int) -> set[int]:
    closed: set[int] = set()
    for day in range(week_start, week_start + 7):
        weekday = WEEKDAYS[day % 7]
        if all(hours.is_closed(weekday, service_id) for service_id in hours.services):
            closed.add(day)
    return closed


def _has_weekday_consecutive_rest(
    off_days: set[int] | list[int], week_start: int, closed: set[int] | None = None
) -> bool:
    closed_days = set(closed or ())
    rest = set(off_days) | closed_days
    pairs = _adjacent_rest_pairs(week_start)
    extra = rest - closed_days
    n_closed = len(closed_days)
    closed_pair = any(left in closed_days and right in closed_days for left, right in pairs)
    if n_closed == 0:
        return any(left in rest and right in rest for left, right in pairs)
    if n_closed == 1:
        closed_day = next(iter(closed_days))
        neighbors = {right for left, right in pairs if left == closed_day} | {
            left for left, right in pairs if right == closed_day
        }
        return bool(extra & neighbors)
    if closed_pair:
        return True
    for closed_day in closed_days:
        neighbors = {right for left, right in pairs if left == closed_day} | {
            left for left, right in pairs if right == closed_day
        }
        if extra & neighbors:
            return True
    return False


def _weekends_off(by_day: dict[int, list[Shift]], week_start: int) -> bool:
    saturday = week_start + 5
    sunday = week_start + 6
    return saturday not in by_day and sunday not in by_day


def _has_weekend_rest_day(
    by_day: dict[int, list[Shift]], week_start: int, hours: RestaurantHours
) -> bool:
    saturday = week_start + 5
    sunday = week_start + 6
    closed = _closed_days(hours, week_start)
    sat_off = saturday not in by_day or saturday in closed
    sun_off = sunday not in by_day or sunday in closed
    return sat_off or sun_off


def _service_count(by_day: dict[int, list[Shift]], week_start: int, service_id: str) -> int:
    return sum(
        1
        for day in range(week_start, week_start + 7)
        for item in by_day.get(day, [])
        if item.service_id == service_id
    )


def _wellbeing_warnings(draft: PlanningDraft) -> list[Warning]:
    warnings: list[Warning] = []
    grouped = _shifts_by_employee(draft)
    for employee in draft.employees:
        wish = employee.wellbeing
        shifts = grouped.get(employee.id, [])
        by_day: dict[int, list[Shift]] = {}
        for shift in shifts:
            by_day.setdefault(shift.day_index, []).append(shift)

        if wish.consecutive_rest:
            for week_start in range(0, draft.horizon_days, 7):
                offs = {day for day in range(week_start, week_start + 7) if day not in by_day}
                closed = _closed_days(draft.hours, week_start)
                if not _has_weekday_consecutive_rest(offs, week_start, closed):
                    warnings.append(
                        _warning(
                            WarningSeverity.SOUHAIT,
                            "consecutive_rest_days",
                            {"week_start": week_start},
                            employee_id=employee.id,
                            day_index=week_start,
                        )
                    )

        if wish.weekend_rest_day:
            for week_start in range(0, draft.horizon_days, 7):
                if not _has_weekend_rest_day(by_day, week_start, draft.hours):
                    warnings.append(
                        _warning(
                            WarningSeverity.SOUHAIT,
                            "weekend_rest_day",
                            {"week_start": week_start},
                            employee_id=employee.id,
                            day_index=week_start,
                        )
                    )

        if wish.weekend is not None and draft.horizon_days >= 14:
            off_even = _weekends_off(by_day, 0)
            off_odd = _weekends_off(by_day, 7)
            if wish.weekend is WeekendChoice.EVERY_TWO and off_even == off_odd:
                warnings.append(
                    _warning(
                        WarningSeverity.SOUHAIT,
                        "weekend_every_two_weeks",
                        {"off_week_0": off_even, "off_week_7": off_odd},
                        employee_id=employee.id,
                    )
                )
            if wish.weekend is WeekendChoice.EVEN and not (off_even and not off_odd):
                warnings.append(
                    _warning(
                        WarningSeverity.SOUHAIT,
                        "weekend_even_weeks",
                        {"off_week_0": off_even, "off_week_7": off_odd},
                        employee_id=employee.id,
                    )
                )
            if wish.weekend is WeekendChoice.ODD and not (off_odd and not off_even):
                warnings.append(
                    _warning(
                        WarningSeverity.SOUHAIT,
                        "weekend_odd_weeks",
                        {"off_week_0": off_even, "off_week_7": off_odd},
                        employee_id=employee.id,
                    )
                )

        service_codes = {
            ServiceName.MORNING.value: "max_mornings",
            ServiceName.MIDDAY.value: "max_middays",
            ServiceName.EVENING.value: "max_evenings",
        }
        for service_id, limit in wish.max_services.items():
            code = service_codes[service_id]
            for week_start in range(0, draft.horizon_days, 7):
                count = _service_count(by_day, week_start, service_id)
                if count > limit:
                    warnings.append(
                        _warning(
                            WarningSeverity.SOUHAIT,
                            code,
                            {
                                "count": count,
                                "limit": limit,
                                "week_start": week_start,
                                "service_id": service_id,
                                "day_indexes": _day_indexes_with_service(by_day, week_start, service_id),
                            },
                            employee_id=employee.id,
                            day_index=week_start,
                        )
                    )

        max_coupures = wish.max_coupures_per_week
        if max_coupures is not None:
            for week_start in range(0, draft.horizon_days, 7):
                coupures = _coupure_count_in_week(grouped.get(employee.id, ()), employee.id, week_start)
                if coupures > max_coupures:
                    warnings.append(
                        _warning(
                            WarningSeverity.SOUHAIT,
                            "max_coupures",
                            {"count": coupures, "limit": max_coupures, "week_start": week_start},
                            employee_id=employee.id,
                            day_index=week_start,
                        )
                    )
    return warnings


def _contract_hours_warnings(draft: PlanningDraft) -> list[Warning]:
    warnings: list[Warning] = []
    grouped = _shifts_by_employee(draft)
    for employee in draft.employees:
        for week_start in range(0, draft.horizon_days, 7):
            hours = sum(
                shift.duration_hours
                for shift in grouped.get(employee.id, [])
                if week_start <= shift.day_index < week_start + 7
            )
            if abs(hours - employee.contractual_hours_per_week) > 0.5:
                warnings.append(
                    _warning(
                        WarningSeverity.SOUHAIT,
                        "contract_hours",
                        {
                            "hours": _qty(hours),
                            "contracted": _qty(employee.contractual_hours_per_week),
                            "week_start": week_start,
                        },
                        employee_id=employee.id,
                        day_index=week_start,
                    )
                )
    return warnings


def rank_candidates(
    draft: PlanningDraft,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    start_minutes: int,
    end_minutes: int,
    post_level: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    occupied = {
        shift.employee_id
        for shift in draft.assignments
        if shift.day_index == day_index
        and shift.start_minutes < end_minutes
        and start_minutes < shift.end_minutes
    }
    for employee in draft.employees:
        if employee.team != team or employee.level < post_level:
            continue
        if employee.id in occupied:
            continue
        trial_shift = Shift(
            employee_id=employee.id,
            day_index=day_index,
            weekday=weekday,
            service_id=service_id,
            team=team,
            start_minutes=start_minutes,
            end_minutes=end_minutes,
            post_level=post_level,
        )
        trial = draft.with_assignments(draft.assignments + (trial_shift,))
        result = evaluate(trial)
        candidates.append(
            Candidate(
                employee=employee,
                result=result,
                overqualification=employee.level - post_level,
            )
        )
    candidates.sort(key=lambda item: (item.interdit_count, item.souhait_count, item.overqualification, item.employee.id))
    return candidates


def swap_shifts(draft: PlanningDraft, first: Shift, second: Shift) -> EngineResult:
    remaining = [shift for shift in draft.assignments if shift not in (first, second)]
    moved_a = replace(second, employee_id=first.employee_id)
    moved_b = replace(first, employee_id=second.employee_id)
    trial = draft.with_assignments(tuple(remaining + [moved_a, moved_b]))
    return evaluate(trial)


def _unavailable(employee: Employee, weekday: str, service_id: str, start_minutes: int) -> bool:
    return any(pattern.blocks(weekday, service_id) for pattern in employee.unavailabilities)


def _hours_in_week(assignments: list[Shift], employee_id: str, day_index: int) -> float:
    week_start = (day_index // 7) * 7
    return sum(
        shift.duration_hours
        for shift in assignments
        if shift.employee_id == employee_id and week_start <= shift.day_index < week_start + 7
    )


def _hours_on_day(assignments: list[Shift], employee_id: str, day_index: int) -> float:
    return sum(
        shift.duration_hours
        for shift in assignments
        if shift.employee_id == employee_id and shift.day_index == day_index
    )


def _has_overlap(assignments: list[Shift], trial: Shift) -> bool:
    return any(trial.overlaps(existing) for existing in assignments if existing.employee_id == trial.employee_id)


def _rest_between_ok(assignments: list[Shift], trial: Shift) -> bool:
    needed = MIN_REST_BETWEEN_DAYS_HOURS * 60
    same_person = [shift for shift in assignments if shift.employee_id == trial.employee_id]
    prev_day = (trial.day_index - 1) % CYCLE_DAYS if trial.day_index == 0 else trial.day_index - 1
    next_day = (trial.day_index + 1) % CYCLE_DAYS
    prev_shifts = [shift for shift in same_person if shift.day_index == prev_day]
    next_shifts = [shift for shift in same_person if shift.day_index == next_day]
    if prev_shifts:
        last = max(shift.end_minutes for shift in prev_shifts)
        rest = (24 * 60 - last) + trial.start_minutes
        if rest < needed:
            return False
    if next_shifts:
        first = min(shift.start_minutes for shift in next_shifts)
        rest = (24 * 60 - trial.end_minutes) + first
        if rest < needed:
            return False
    return True


def _teammate_under_hours(
    assignments: list[Shift], employees: list[Employee], employee: Employee, day_index: int
) -> bool:
    for other in employees:
        if other.team != employee.team or other.id == employee.id:
            continue
        if _hours_in_week(assignments, other.id, day_index) + 1e-9 < other.contractual_hours_per_week:
            return True
    return False


def _max_coupures_per_week(employee: Employee) -> int | None:
    return employee.wellbeing.max_coupures_per_week


def _has_gap(shifts: list[Shift]) -> bool:
    if len(shifts) < 2:
        return False
    ordered = sorted(shifts, key=lambda item: item.start_minutes)
    return any(second.start_minutes - first.end_minutes > 0 for first, second in zip(ordered, ordered[1:]))


def _coupure_count_in_week(assignments: list[Shift] | tuple[Shift, ...], employee_id: str, week_start: int) -> int:
    count = 0
    for day in range(week_start, week_start + 7):
        day_shifts = [shift for shift in assignments if shift.employee_id == employee_id and shift.day_index == day]
        if _has_gap(day_shifts):
            count += 1
    return count


def _already_on_day(assignments: list[Shift], employee_id: str, day_index: int) -> bool:
    return any(shift.employee_id == employee_id and shift.day_index == day_index for shift in assignments)


def _pause_within_legal(assignments: list[Shift], trial: Shift) -> bool:
    day_shifts = [
        shift
        for shift in assignments
        if shift.employee_id == trial.employee_id and shift.day_index == trial.day_index
    ]
    ordered = sorted(day_shifts + [trial], key=lambda item: item.start_minutes)
    limit = MAX_COUPURE_HOURS * 60
    for first, second in zip(ordered, ordered[1:]):
        gap = second.start_minutes - first.end_minutes
        if gap > limit:
            return False
    return True


def _would_exceed_contract(assignments: list[Shift], employee: Employee, trial: Shift) -> bool:
    return (
        _hours_in_week(assignments, employee.id, trial.day_index) + trial.duration_hours
        > employee.contractual_hours_per_week + 1e-9
    )


def _would_exceed_coupures(assignments: list[Shift], employee: Employee, trial: Shift) -> bool:
    cap = _max_coupures_per_week(employee)
    if cap is None:
        return False
    week_start = (trial.day_index // 7) * 7
    with_trial = [*assignments, trial]
    return _coupure_count_in_week(with_trial, employee.id, week_start) > cap


def _would_exceed_max_services(assignments: list[Shift], employee: Employee, trial: Shift) -> bool:
    if trial.service_id not in employee.wellbeing.max_services:
        return False
    week_start = (trial.day_index // 7) * 7
    by_day: dict[int, list[Shift]] = {}
    for shift in assignments:
        if shift.employee_id == employee.id:
            by_day.setdefault(shift.day_index, []).append(shift)
    return _service_count(by_day, week_start, trial.service_id) + 1 > employee.wellbeing.max_services[trial.service_id]


def _assigned_window(
    employee: Employee, window: PostWindow, structure: ServiceStructure
) -> PostWindow | None:
    stretched = stretch_to_min_shift(window, employee.min_shift_hours, structure)
    duration = stretched.end_minutes - stretched.start_minutes
    if duration < int(employee.min_shift_hours * 60):
        return None
    return stretched


def _window_meets_min_shift(
    employee: Employee, window: PostWindow, structure: ServiceStructure
) -> bool:
    return _assigned_window(employee, window, structure) is not None


def _eligible_for_service(
    employee: Employee, draft: PlanningDraft, weekday: str, service_id: str, team: Team
) -> bool:
    if employee.team != team:
        return False
    structure = draft.structure_for(team, service_id, weekday)
    if structure is None:
        return False
    windows = derive_post_windows(structure)
    if not windows:
        return False
    return any(
        employee.level >= window.level
        and _window_meets_min_shift(employee, window, structure)
        and not _unavailable(
            employee,
            weekday,
            service_id,
            (_assigned_window(employee, window, structure) or window).start_minutes,
        )
        for window in windows
    )


def _staffing_needs(
    draft: PlanningDraft,
) -> list[tuple[int, Team, str, int, tuple[str, ...], int]]:
    """(day_index, team, service_id, posts_needed, eligible ids, min post minutes)."""
    needs: list[tuple[int, Team, str, int, tuple[str, ...], int]] = []
    for day_index in range(CYCLE_DAYS):
        weekday = WEEKDAYS[day_index % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                continue
            for team in Team:
                structure = draft.structure_for(team, service_id, weekday)
                if structure is None:
                    continue
                windows = derive_post_windows(structure)
                if not windows:
                    continue
                assignable = [
                    window
                    for window in windows
                    if any(
                        employee.team == team
                        and employee.level >= window.level
                        and day_index not in employee.forced_off_days
                        and _window_meets_min_shift(employee, window, structure)
                        and not _unavailable(
                            employee,
                            weekday,
                            service_id,
                            (_assigned_window(employee, window, structure) or window).start_minutes,
                        )
                        for employee in draft.employees
                    )
                ]
                if not assignable:
                    continue
                eligible = tuple(
                    employee.id
                    for employee in draft.employees
                    if _eligible_for_service(employee, draft, weekday, service_id, team)
                    and day_index not in employee.forced_off_days
                )
                stretched_minutes = []
                for window in assignable:
                    for employee in draft.employees:
                        if employee.team != team or employee.level < window.level:
                            continue
                        assigned = _assigned_window(employee, window, structure)
                        if assigned is not None:
                            stretched_minutes.append(assigned.end_minutes - assigned.start_minutes)
                shortest = min(
                    stretched_minutes,
                    default=min(window.end_minutes - window.start_minutes for window in assignable),
                )
                needs.append((day_index, team, service_id, len(assignable), eligible, shortest))
    return needs


def _soft_penalty(
    draft: PlanningDraft,
    assignments: list[Shift],
    employee: Employee,
    trial: Shift,
    pool_index: int = 0,
) -> tuple:
    """Lower is better. Hard-ineligible callers must skip before this."""
    duration = trial.duration_hours
    week_hours = _hours_in_week(assignments, employee.id, trial.day_index)
    day_hours = _hours_on_day(assignments, employee.id, trial.day_index)
    max_daily = MAX_DAILY_HOURS_CUISINE if employee.team == Team.CUISINE else MAX_DAILY_HOURS_SALLE
    over_week_cap = week_hours + duration > MAX_WEEKLY_HOURS + 1e-9
    over_day_cap = day_hours + duration > max_daily + 1e-9
    rest_bad = not _rest_between_ok(assignments, trial)
    pause_bad = not _pause_within_legal(assignments, trial)
    overqual = employee.level - trial.post_level
    current_ratio = week_hours / max(employee.contractual_hours_per_week, 1.0)
    projected_ratio = (week_hours + duration) / max(employee.contractual_hours_per_week, 1.0)
    creates_coupure = _creates_coupure(assignments, trial)
    return (
        int(over_week_cap or over_day_cap or rest_bad or pause_bad),
        current_ratio,
        int(creates_coupure),
        overqual,
        projected_ratio,
        pool_index,
        employee.id,
    )


def _creates_coupure(assignments: list[Shift], trial: Shift) -> bool:
    day_shifts = [
        shift
        for shift in assignments
        if shift.employee_id == trial.employee_id and shift.day_index == trial.day_index
    ]
    if not day_shifts:
        return False
    return _has_gap([*day_shifts, trial])


def _can_fill_window(
    draft: PlanningDraft,
    assignments: list[Shift],
    employee: Employee,
    *,
    window: PostWindow,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
) -> bool:
    if employee.team != team or employee.level < window.level:
        return False
    structure = draft.structure_for(team, service_id, weekday)
    if structure is None:
        return False
    assigned = _assigned_window(employee, window, structure)
    if assigned is None:
        return False
    if day_index in off_days.get(employee.id, set()):
        return False
    if _unavailable(employee, weekday, service_id, assigned.start_minutes):
        return False
    trial = Shift(
        employee_id=employee.id,
        day_index=day_index,
        weekday=weekday,
        service_id=service_id,
        team=team,
        start_minutes=assigned.start_minutes,
        end_minutes=assigned.end_minutes,
        post_level=window.level,
    )
    if _has_overlap(assignments, trial):
        return False
    if _would_exceed_max_services(assignments, employee, trial):
        return False
    if _would_exceed_coupures(assignments, employee, trial):
        return False
    if _would_exceed_contract(assignments, employee, trial) and _teammate_under_hours(
        assignments, employee_pool, employee, day_index
    ):
        return False
    penalty = _soft_penalty(draft, assignments, employee, trial)
    return penalty[0] == 0


def _is_unique_for_earlier_hole(
    draft: PlanningDraft,
    assignments: list[Shift],
    employee: Employee,
    *,
    remaining_windows: tuple[PostWindow, ...],
    current_start: int,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
) -> bool:
    for hole in remaining_windows:
        if hole.start_minutes >= current_start:
            continue
        able = [
            other
            for other in employee_pool
            if _can_fill_window(
                draft,
                assignments,
                other,
                window=hole,
                day_index=day_index,
                weekday=weekday,
                service_id=service_id,
                team=team,
                off_days=off_days,
                employee_pool=employee_pool,
            )
        ]
        if [other.id for other in able] == [employee.id]:
            return True
    return False


def _pick_for_post(
    draft: PlanningDraft,
    assignments: list[Shift],
    *,
    employee_pool: list[Employee],
    window_level: int,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    start_minutes: int,
    end_minutes: int,
    off_days: dict[str, set[int]],
    remaining_windows: tuple[PostWindow, ...] = (),
) -> tuple[Employee, PostWindow] | None:
    structure = draft.structure_for(team, service_id, weekday)
    if structure is None:
        return None
    hole = PostWindow(level=window_level, start_minutes=start_minutes, end_minutes=end_minutes)
    scored: list[tuple] = []
    for employee in employee_pool:
        if employee.team != team or employee.level < window_level:
            continue
        assigned = _assigned_window(employee, hole, structure)
        if assigned is None:
            continue
        occupied = {
            shift.employee_id
            for shift in assignments
            if shift.day_index == day_index
            and shift.start_minutes < assigned.end_minutes
            and assigned.start_minutes < shift.end_minutes
        }
        if day_index in off_days.get(employee.id, set()):
            continue
        if employee.id in occupied:
            continue
        if _unavailable(employee, weekday, service_id, assigned.start_minutes):
            continue
        trial = Shift(
            employee_id=employee.id,
            day_index=day_index,
            weekday=weekday,
            service_id=service_id,
            team=team,
            start_minutes=assigned.start_minutes,
            end_minutes=assigned.end_minutes,
            post_level=window_level,
        )
        if _has_overlap(assignments, trial):
            continue
        if _would_exceed_max_services(assignments, employee, trial):
            continue
        if _would_exceed_coupures(assignments, employee, trial):
            continue
        if _would_exceed_contract(assignments, employee, trial) and _teammate_under_hours(
            assignments, employee_pool, employee, day_index
        ):
            continue
        ranks = {person.id: index for index, person in enumerate(employee_pool)}
        scored.append(
            (
                _soft_penalty(
                    draft,
                    assignments,
                    employee,
                    trial,
                    pool_index=ranks[employee.id],
                ),
                employee,
                assigned,
            )
        )
    if not scored:
        return None
    scored.sort(key=lambda item: item[0])
    legal = [(employee, assigned) for penalty, employee, assigned in scored if penalty[0] == 0]
    if not legal:
        return None
    if remaining_windows and len(legal) > 1:
        kept = [
            pair
            for pair in legal
            if not _is_unique_for_earlier_hole(
                draft,
                assignments,
                pair[0],
                remaining_windows=remaining_windows,
                current_start=start_minutes,
                day_index=day_index,
                weekday=weekday,
                service_id=service_id,
                team=team,
                off_days=off_days,
                employee_pool=employee_pool,
            )
        ]
        if kept:
            legal = kept
    return legal[0]


def _daily_cap_minutes(employee: Employee) -> int:
    legal = MAX_DAILY_HOURS_CUISINE if employee.team == Team.CUISINE else MAX_DAILY_HOURS_SALLE
    return int(min(legal, employee.contractual_hours_per_week) * 60)


def _median_int(values: list[int]) -> int:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return 60
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) // 2


def _eligible_post_durations(draft: PlanningDraft, employee: Employee, week_start: int) -> list[int]:
    durations: list[int] = []
    for day in range(week_start, week_start + 7):
        if day in employee.forced_off_days:
            continue
        weekday = WEEKDAYS[day % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                continue
            structure = draft.structure_for(employee.team, service_id, weekday)
            if structure is None:
                continue
            if not _eligible_for_service(employee, draft, weekday, service_id, employee.team):
                continue
            for window in derive_post_windows(structure):
                if employee.level < window.level:
                    continue
                assigned = _assigned_window(employee, window, structure)
                if assigned is None:
                    continue
                duration = assigned.end_minutes - assigned.start_minutes
                if duration > 0:
                    durations.append(duration)
    return durations


def _max_shifts_for_hours(contract_hours: float, typical_minutes: int, shortest_minutes: int) -> int:
    """How many services a contract can cover: floor(hours / typical post), at least one if the shortest still fits."""
    contract_minutes = int(contract_hours * 60)
    typical = typical_minutes if typical_minutes > 0 else (shortest_minutes or 60)
    shortest = shortest_minutes if shortest_minutes > 0 else typical
    max_shifts = contract_minutes // typical
    if max_shifts == 0 and contract_minutes >= shortest:
        return 1
    return max_shifts


class _RestCollector(cp_model.CpSolverSolutionCallback):
    """Collect unique rest calendars (who is off which day)."""

    def __init__(
        self,
        work: dict[tuple[str, int], cp_model.IntVar],
        employees: tuple[Employee, ...],
        limit: int | None = None,
        deadline: float | None = None,
        on_unique: Callable[[dict[str, set[int]]], None] | None = None,
        store: bool = True,
    ):
        super().__init__()
        self._work = work
        self._employees = employees
        self._limit = limit
        self._deadline = deadline
        self._on_unique = on_unique
        self._store = store
        self.patterns: list[dict[str, set[int]]] = []
        self._seen: set[tuple] = set()
        self.unique_count = 0

    def on_solution_callback(self) -> None:
        fingerprint = []
        off: dict[str, set[int]] = {}
        for employee in self._employees:
            days = [
                day
                for day in range(CYCLE_DAYS)
                if self.Value(self._work[employee.id, day]) == 0
            ]
            fingerprint.append((employee.id, tuple(days)))
            off[employee.id] = set(days)
        key = tuple(fingerprint)
        if key in self._seen:
            return
        self._seen.add(key)
        self.unique_count += 1
        if self._store:
            self.patterns.append(off)
        if self._on_unique is not None:
            self._on_unique(off)
        if self._limit is not None and self.unique_count >= self._limit:
            self.StopSearch()
            return
        if self._deadline is not None and time.perf_counter() >= self._deadline:
            self.StopSearch()


def _build_rest_model(
    draft: PlanningDraft,
    *,
    hard_coverage: bool,
    locks: tuple[Shift, ...] | list[Shift] = (),
) -> tuple[cp_model.CpModel, dict[tuple[str, int], cp_model.IntVar], list]:
    """14-day rest model. Coverage is per service. No sequential week A then B."""
    if SEQUENTIAL_WEEK_SOLVE:
        raise RuntimeError("Sequential week solves are forbidden")
    model = cp_model.CpModel()
    work: dict[tuple[str, int], cp_model.IntVar] = {}
    lock_days: dict[str, set[int]] = {}
    lock_cover: dict[tuple[int, Team, str], int] = {}
    for shift in locks:
        lock_days.setdefault(shift.employee_id, set()).add(shift.day_index)
        key = (shift.day_index, shift.team, shift.service_id)
        lock_cover[key] = lock_cover.get(key, 0) + 1
    for employee in draft.employees:
        for day in range(CYCLE_DAYS):
            work[employee.id, day] = model.NewBoolVar(f"work_{employee.id}_{day}")
            weekday = WEEKDAYS[day % 7]
            if all(draft.hours.is_closed(weekday, service_id) for service_id in draft.hours.services):
                model.Add(work[employee.id, day] == 0)
            if day in employee.forced_off_days:
                model.Add(work[employee.id, day] == 0)
            if day in lock_days.get(employee.id, set()):
                model.Add(work[employee.id, day] == 1)

    covers_by_emp_day: dict[tuple[str, int], list] = {}
    minutes_by_emp_day: dict[tuple[str, int], list[tuple[int, cp_model.IntVar]]] = {}
    unders: list = []
    for day_index, team, service_id, posts, eligible_ids, shortest in _staffing_needs(draft):
        if not eligible_ids:
            continue
        service_covers = []
        for employee_id in eligible_ids:
            var = model.NewBoolVar(f"cover_{employee_id}_{day_index}_{team.value}_{service_id}")
            model.Add(var <= work[employee_id, day_index])
            covers_by_emp_day.setdefault((employee_id, day_index), []).append(var)
            minutes_by_emp_day.setdefault((employee_id, day_index), []).append((shortest, var))
            service_covers.append(var)
        held = lock_cover.get((day_index, team, service_id), 0)
        need = max(0, min(posts, len(eligible_ids)) - held)
        if need == 0:
            continue
        if hard_coverage:
            model.Add(sum(service_covers) >= need)
        else:
            under = model.NewIntVar(0, need, f"under_{day_index}_{team.value}_{service_id}")
            model.Add(sum(service_covers) + under >= need)
            unders.append(under)

    for employee in draft.employees:
        for day in range(CYCLE_DAYS):
            covers = covers_by_emp_day.get((employee.id, day), [])
            if not covers:
                model.Add(work[employee.id, day] == 0)
                continue
            model.Add(sum(covers) >= work[employee.id, day])
            cap = _daily_cap_minutes(employee)
            weighted = minutes_by_emp_day[(employee.id, day)]
            model.Add(sum(minutes * var for minutes, var in weighted) <= cap)

    for employee in draft.employees:
        for week_start in (0, 7):
            week_terms = [
                minutes * var
                for day in range(week_start, week_start + 7)
                for minutes, var in minutes_by_emp_day.get((employee.id, day), [])
            ]
            if week_terms:
                model.Add(sum(week_terms) <= int(employee.contractual_hours_per_week * 60))

    for employee in draft.employees:
        for week_start in (0, 7):
            already_days = set()
            for day in range(week_start, week_start + 7):
                weekday = WEEKDAYS[day % 7]
                closed = all(
                    draft.hours.is_closed(weekday, service_id) for service_id in draft.hours.services
                )
                unworkable = not covers_by_emp_day.get((employee.id, day), [])
                if closed or day in employee.forced_off_days or unworkable:
                    already_days.add(day)
            open_days = [day for day in range(week_start, week_start + 7) if day not in already_days]
            model.Add(sum(1 - work[employee.id, day] for day in range(week_start, week_start + 7)) >= REST_DAYS_PER_WEEK)
            durations = _eligible_post_durations(draft, employee, week_start)
            typical = _median_int(durations)
            shortest = min(durations) if durations else 60
            max_shifts = _max_shifts_for_hours(employee.contractual_hours_per_week, typical, shortest)
            cover_vars = [
                var
                for day in range(week_start, week_start + 7)
                for var in covers_by_emp_day.get((employee.id, day), [])
            ]
            if cover_vars:
                model.Add(sum(cover_vars) <= max_shifts)
            if not open_days:
                continue
            hours_open_rest = max(0, len(open_days) - max_shifts)
            legal_open_rest = max(0, REST_DAYS_PER_WEEK - len(already_days))
            wants_pair = employee.wellbeing.consecutive_rest
            has_pair = _has_weekday_consecutive_rest(already_days, week_start, _closed_days(draft.hours, week_start))
            if wants_pair and not has_pair:
                legal_open_rest = max(legal_open_rest, 2)
            open_rest_target = min(len(open_days), max(legal_open_rest, hours_open_rest))
            model.Add(sum(1 - work[employee.id, day] for day in open_days) == open_rest_target)
        if employee.wellbeing.consecutive_rest:
            for week_start in (0, 7):
                pair_hits = []
                for left, right in _adjacent_rest_pairs(week_start):
                    pair = model.NewBoolVar(f"pair_{employee.id}_{week_start}_{left}_{right}")
                    model.Add(work[employee.id, left] == 0).OnlyEnforceIf(pair)
                    model.Add(work[employee.id, right] == 0).OnlyEnforceIf(pair)
                    pair_hits.append(pair)
                model.Add(sum(pair_hits) >= 1)
        if employee.wellbeing.weekend is not None:
            even_off = model.NewBoolVar(f"we_even_{employee.id}")
            odd_off = model.NewBoolVar(f"we_odd_{employee.id}")
            model.Add(work[employee.id, 5] + work[employee.id, 6] == 0).OnlyEnforceIf(even_off)
            model.Add(work[employee.id, 5] + work[employee.id, 6] >= 1).OnlyEnforceIf(even_off.Not())
            model.Add(work[employee.id, 12] + work[employee.id, 13] == 0).OnlyEnforceIf(odd_off)
            model.Add(work[employee.id, 12] + work[employee.id, 13] >= 1).OnlyEnforceIf(odd_off.Not())
            if employee.wellbeing.weekend is WeekendChoice.EVERY_TWO:
                model.Add(even_off + odd_off == 1)
            elif employee.wellbeing.weekend is WeekendChoice.EVEN:
                model.Add(even_off == 1)
                model.Add(odd_off == 0)
            else:
                model.Add(odd_off == 1)
                model.Add(even_off == 0)
        if employee.wellbeing.weekend_rest_day:
            for week_start in (0, 7):
                saturday = week_start + 5
                sunday = week_start + 6
                model.Add(work[employee.id, saturday] + work[employee.id, sunday] <= 1)
    return model, work, unders


def _fallback_rest_days(draft: PlanningDraft) -> dict[str, set[int]]:
    off: dict[str, set[int]] = {employee.id: set() for employee in draft.employees}
    for employee in draft.employees:
        off[employee.id].update({0, 1, 7, 8})
        if employee.wellbeing.weekend is WeekendChoice.EVERY_TWO:
            off[employee.id].update({5, 6})
        elif employee.wellbeing.weekend is WeekendChoice.EVEN:
            off[employee.id].update({5, 6})
        elif employee.wellbeing.weekend is WeekendChoice.ODD:
            off[employee.id].update({12, 13})
        if employee.wellbeing.weekend_rest_day:
            for week_start in (0, 7):
                closed = _closed_days(draft.hours, week_start)
                saturday = week_start + 5
                sunday = week_start + 6
                if saturday not in closed and sunday not in closed:
                    off[employee.id].add(saturday)
    return off


def _off_from_solver(
    solver: cp_model.CpSolver, work: dict[tuple[str, int], cp_model.IntVar], draft: PlanningDraft
) -> dict[str, set[int]]:
    off: dict[str, set[int]] = {employee.id: set() for employee in draft.employees}
    for employee in draft.employees:
        for day in range(CYCLE_DAYS):
            if solver.Value(work[employee.id, day]) == 0:
                off[employee.id].add(day)
    return off


def _collect_rest_solutions(
    model: cp_model.CpModel,
    work: dict[tuple[str, int], cp_model.IntVar],
    draft: PlanningDraft,
    *,
    limit: int | None,
    seconds: float,
    deadline: float | None = None,
    on_unique: Callable[[dict[str, set[int]]], None] | None = None,
    store: bool = True,
) -> _RestCollector:
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    cap = deadline if deadline is not None else time.perf_counter() + seconds
    solver.parameters.max_time_in_seconds = max(0.01, cap - time.perf_counter())
    collector = _RestCollector(
        work,
        draft.employees,
        limit=limit,
        deadline=cap,
        on_unique=on_unique,
        store=store,
    )
    if limit == 1:
        status = solver.Solve(model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            off = _off_from_solver(solver, work, draft)
            collector.unique_count = 1
            if store:
                collector.patterns = [off]
            if on_unique is not None:
                on_unique(off)
        return collector
    solver.parameters.enumerate_all_solutions = True
    solver.Solve(model, collector)
    return collector


def _slack_or_fallback(draft: PlanningDraft, seconds: float) -> dict[str, set[int]]:
    slack, slack_work, unders = _build_rest_model(draft, hard_coverage=False)
    if unders:
        slack.Minimize(sum(unders))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.01, seconds)
    solver.parameters.num_search_workers = 1
    status = solver.Solve(slack)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return _fallback_rest_days(draft)
    return _off_from_solver(solver, slack_work, draft)


def _enumerate_rest_days(
    draft: PlanningDraft, search: SearchEffort = SearchEffort.OPTIMIZED
) -> list[dict[str, set[int]]]:
    """Covering rest calendars, bounded by search effort."""
    limit = SEARCH_CALENDAR_LIMITS[search]
    seconds = SEARCH_SECONDS[search]
    hard, work, _unders = _build_rest_model(draft, hard_coverage=True)
    collector = _collect_rest_solutions(hard, work, draft, limit=limit, seconds=seconds)
    if collector.unique_count:
        return collector.patterns
    return [_slack_or_fallback(draft, seconds)]


def _plan_rest_days(draft: PlanningDraft, seed: int = 0) -> dict[str, set[int]]:
    """One legal rest calendar (first of the covering enumeration)."""
    del seed
    return _enumerate_rest_days(draft)[0]


def _iter_service_windows(draft: PlanningDraft, start_day: int = 0):
    for offset in range(CYCLE_DAYS):
        day_index = (start_day + offset) % CYCLE_DAYS
        weekday = WEEKDAYS[day_index % 7]
        for service_id in draft.hours.services:
            if draft.hours.is_closed(weekday, service_id):
                continue
            for team in Team:
                structure = draft.structure_for(team, service_id, weekday)
                if structure is None:
                    continue
                windows = sorted(
                    derive_post_windows(structure),
                    key=lambda item: (-item.level, item.start_minutes),
                )
                yield day_index, weekday, service_id, team, windows


@dataclass(frozen=True)
class _FillWindowJob:
    eligible_count: int
    day_index: int
    weekday: str
    service_id: str
    team: Team
    window: PostWindow
    cell_windows: tuple[PostWindow, ...]


def _fill_window_jobs(
    draft: PlanningDraft,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
    start_day: int = 0,
) -> list[_FillWindowJob]:
    """Windows ordered fewest static eligibles first (core-2)."""
    service_rank = {service_id: index for index, service_id in enumerate(draft.hours.services)}
    jobs: list[_FillWindowJob] = []
    for day_index, weekday, service_id, team, windows in _iter_service_windows(draft, start_day):
        cell_windows = tuple(windows)
        for window in windows:
            eligible = sum(
                1
                for employee in employee_pool
                if _can_fill_window(
                    draft,
                    [],
                    employee,
                    window=window,
                    day_index=day_index,
                    weekday=weekday,
                    service_id=service_id,
                    team=team,
                    off_days=off_days,
                    employee_pool=employee_pool,
                )
            )
            jobs.append(
                _FillWindowJob(
                    eligible_count=eligible,
                    day_index=day_index,
                    weekday=weekday,
                    service_id=service_id,
                    team=team,
                    window=window,
                    cell_windows=cell_windows,
                )
            )
    jobs.sort(
        key=lambda job: (
            job.eligible_count,
            job.day_index,
            service_rank[job.service_id],
            -job.window.level,
            job.window.start_minutes,
            job.team.value,
        )
    )
    return jobs


def _shift_covers_window(
    shift: Shift,
    window: PostWindow,
    *,
    day_index: int,
    service_id: str,
    team: Team,
) -> bool:
    return (
        shift.day_index == day_index
        and shift.service_id == service_id
        and shift.team == team
        and shift.post_level == window.level
        and shift.start_minutes <= window.start_minutes
        and shift.end_minutes >= window.end_minutes
    )


def _taken_windows(
    assignments: list[Shift],
    *,
    day_index: int,
    service_id: str,
    team: Team,
    windows: list[PostWindow] | tuple[PostWindow, ...],
) -> set[PostWindow]:
    taken: set[PostWindow] = set()
    used: set[int] = set()
    for window in sorted(windows, key=lambda item: (-item.level, item.start_minutes)):
        for index, shift in enumerate(assignments):
            if index in used:
                continue
            if _shift_covers_window(
                shift, window, day_index=day_index, service_id=service_id, team=team
            ):
                taken.add(window)
                used.add(index)
                break
    return taken


def _append_shift(
    assignments: list[Shift],
    employee: Employee,
    *,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    window: PostWindow,
) -> None:
    assignments.append(
        Shift(
            employee_id=employee.id,
            day_index=day_index,
            weekday=weekday,
            service_id=service_id,
            team=team,
            start_minutes=window.start_minutes,
            end_minutes=window.end_minutes,
            post_level=window.level,
        )
    )


def _lock_key(shift: Shift) -> tuple:
    return (
        shift.employee_id,
        shift.day_index,
        shift.service_id,
        shift.team,
        shift.start_minutes,
        shift.end_minutes,
        shift.post_level,
    )


def _fill_assignments(
    draft: PlanningDraft,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
    start_day: int = 0,
    locks: tuple[Shift, ...] | list[Shift] = (),
) -> list[Shift]:
    assignments: list[Shift] = list(locks)
    locked = frozenset(_lock_key(shift) for shift in locks)
    jobs = _fill_window_jobs(draft, off_days, employee_pool, start_day)
    pending_by_cell: dict[tuple[int, str, Team], list[PostWindow]] = {}
    for job in jobs:
        cell = (job.day_index, job.service_id, job.team)
        pending_by_cell.setdefault(cell, list(job.cell_windows))
    for job in jobs:
        pending = pending_by_cell[(job.day_index, job.service_id, job.team)]
        taken = _taken_windows(
            assignments,
            day_index=job.day_index,
            service_id=job.service_id,
            team=job.team,
            windows=job.cell_windows,
        )
        if job.window in taken:
            pending.remove(job.window)
            continue
        picked = _pick_for_post(
            draft,
            assignments,
            employee_pool=employee_pool,
            window_level=job.window.level,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            start_minutes=job.window.start_minutes,
            end_minutes=job.window.end_minutes,
            off_days=off_days,
            remaining_windows=tuple(pending),
        )
        pending.remove(job.window)
        if picked is None:
            continue
        chosen, assigned = picked
        _append_shift(
            assignments,
            chosen,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            window=assigned,
        )
    _repair_holes(
        draft,
        assignments,
        off_days,
        employee_pool,
        start_day=start_day,
        locked=locked,
    )
    return assignments


def _displace_for_window(
    draft: PlanningDraft,
    assignments: list[Shift],
    *,
    hole: PostWindow,
    day_index: int,
    weekday: str,
    service_id: str,
    team: Team,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
    locked: frozenset[tuple] = frozenset(),
) -> bool:
    same_day = [
        shift
        for shift in assignments
        if shift.day_index == day_index and shift.team == team
    ]
    overlapping = [
        shift
        for shift in same_day
        if shift.start_minutes < hole.end_minutes and hole.start_minutes < shift.end_minutes
    ]
    overlap_ids = {id(shift) for shift in overlapping}
    held_order = overlapping + [shift for shift in same_day if id(shift) not in overlap_ids]
    for held in held_order:
        if _lock_key(held) in locked:
            continue
        person = draft.employee(held.employee_id)
        without = [shift for shift in assignments if shift is not held]
        if not _can_fill_window(
            draft,
            without,
            person,
            window=hole,
            day_index=day_index,
            weekday=weekday,
            service_id=service_id,
            team=team,
            off_days=off_days,
            employee_pool=employee_pool,
        ):
            continue
        others = [employee for employee in employee_pool if employee.id != person.id]
        picked = _pick_for_post(
            draft,
            without,
            employee_pool=others,
            window_level=held.post_level,
            day_index=held.day_index,
            weekday=held.weekday,
            service_id=held.service_id,
            team=held.team,
            start_minutes=held.start_minutes,
            end_minutes=held.end_minutes,
            off_days=off_days,
        )
        if picked is None or picked[0].id == person.id:
            continue
        replacement, replacement_window = picked
        hole_structure = draft.structure_for(team, service_id, weekday)
        hole_assigned = (
            _assigned_window(person, hole, hole_structure) if hole_structure is not None else hole
        ) or hole
        assignments[:] = without
        _append_shift(
            assignments,
            replacement,
            day_index=held.day_index,
            weekday=held.weekday,
            service_id=held.service_id,
            team=held.team,
            window=replacement_window,
        )
        _append_shift(
            assignments,
            person,
            day_index=day_index,
            weekday=weekday,
            service_id=service_id,
            team=team,
            window=hole_assigned,
        )
        return True
    return False


def _repair_holes(
    draft: PlanningDraft,
    assignments: list[Shift],
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
    start_day: int = 0,
    locked: frozenset[tuple] = frozenset(),
) -> None:
    for job in _fill_window_jobs(draft, off_days, employee_pool, start_day):
        taken = _taken_windows(
            assignments,
            day_index=job.day_index,
            service_id=job.service_id,
            team=job.team,
            windows=job.cell_windows,
        )
        if job.window in taken:
            continue
        pending = [window for window in job.cell_windows if window not in taken]
        picked = _pick_for_post(
            draft,
            assignments,
            employee_pool=employee_pool,
            window_level=job.window.level,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            start_minutes=job.window.start_minutes,
            end_minutes=job.window.end_minutes,
            off_days=off_days,
            remaining_windows=tuple(pending),
        )
        if picked is not None:
            chosen, assigned = picked
            _append_shift(
                assignments,
                chosen,
                day_index=job.day_index,
                weekday=job.weekday,
                service_id=job.service_id,
                team=job.team,
                window=assigned,
            )
            continue
        _displace_for_window(
            draft,
            assignments,
            hole=job.window,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            off_days=off_days,
            employee_pool=employee_pool,
            locked=locked,
        )


def _hours_miss(draft: PlanningDraft, assignments: tuple[Shift, ...] | list[Shift]) -> float:
    miss = 0.0
    for employee in draft.employees:
        for week_start in (0, 7):
            hours = sum(
                shift.duration_hours
                for shift in assignments
                if shift.employee_id == employee.id and week_start <= shift.day_index < week_start + 7
            )
            miss += abs(hours - employee.contractual_hours_per_week)
    return round(miss, 2)


def _below_role_count(draft: PlanningDraft, assignments: tuple[Shift, ...] | list[Shift]) -> int:
    by_id = {employee.id: employee for employee in draft.employees}
    count = 0
    for shift in assignments:
        person = by_id.get(shift.employee_id)
        if person is not None and person.level > shift.post_level:
            count += 1
    return count


def _overqualification(draft: PlanningDraft, assignments: tuple[Shift, ...] | list[Shift]) -> int:
    total = 0
    by_id = {employee.id: employee for employee in draft.employees}
    for shift in assignments:
        person = by_id.get(shift.employee_id)
        if person is None:
            continue
        total += person.level - shift.post_level
    return total


def _attempt_key(draft: PlanningDraft, result: EngineResult) -> tuple:
    empty = sum(1 for warning in result.warnings if warning.code == "empty_post")
    interdit = len(result.of_severity(WarningSeverity.INTERDIT))
    souhait = len(result.of_severity(WarningSeverity.SOUHAIT))
    return (
        empty,
        interdit,
        _hours_miss(draft, result.assignments),
        souhait,
        _below_role_count(draft, result.assignments),
        _overqualification(draft, result.assignments),
    )


def _seeder_rng(seeder: str, seed_index: int) -> random.Random:
    return random.Random(SEEDERS.index(seeder) * 1_000_003 + seed_index + 1)


def _seed_specs(effort: SearchEffort) -> list[tuple[str, int]]:
    if effort is SearchEffort.MINIMAL:
        return [("empty", 0)]
    copies = 10 if effort is SearchEffort.OPTIMIZED else 50
    specs = [
        (seeder, index)
        for seeder in ("tight-frozen", "tight-dynamic", "high-role", "weekend-scarce")
        for index in range(copies)
    ]
    specs.append(("empty", 0))
    return specs


def _forced_off_days(draft: PlanningDraft) -> dict[str, set[int]]:
    return {employee.id: set(employee.forced_off_days) for employee in draft.employees}


def _window_covered(
    assignments: list[Shift],
    *,
    day_index: int,
    service_id: str,
    team: Team,
    window: PostWindow,
    cell_windows: tuple[PostWindow, ...],
) -> bool:
    return window in _taken_windows(
        assignments,
        day_index=day_index,
        service_id=service_id,
        team=team,
        windows=cell_windows,
    )


def _eligible_count_for_job(
    draft: PlanningDraft,
    assignments: list[Shift],
    job: _FillWindowJob,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
) -> int:
    return sum(
        1
        for employee in employee_pool
        if _can_fill_window(
            draft,
            assignments,
            employee,
            window=job.window,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            off_days=off_days,
            employee_pool=employee_pool,
        )
    )


def _empty_windows(
    draft: PlanningDraft,
    assignments: list[Shift],
    jobs: list[_FillWindowJob],
) -> list[_FillWindowJob]:
    return [
        job
        for job in jobs
        if not _window_covered(
            assignments,
            day_index=job.day_index,
            service_id=job.service_id,
            team=job.team,
            window=job.window,
            cell_windows=job.cell_windows,
        )
    ]


def _versatility(
    draft: PlanningDraft,
    assignments: list[Shift],
    employee: Employee,
    jobs: list[_FillWindowJob],
    current: _FillWindowJob,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
) -> int:
    count = 0
    for job in jobs:
        if (
            job.day_index == current.day_index
            and job.service_id == current.service_id
            and job.team == current.team
            and job.window == current.window
        ):
            continue
        if _can_fill_window(
            draft,
            assignments,
            employee,
            window=job.window,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            off_days=off_days,
            employee_pool=employee_pool,
        ):
            count += 1
    return count


def _try_seed_shift(
    draft: PlanningDraft,
    assignments: list[Shift],
    job: _FillWindowJob,
    off_days: dict[str, set[int]],
    employee_pool: list[Employee],
    empty_jobs: list[_FillWindowJob],
    rng: random.Random,
) -> bool:
    legal: list[Employee] = []
    for employee in employee_pool:
        if _can_fill_window(
            draft,
            assignments,
            employee,
            window=job.window,
            day_index=job.day_index,
            weekday=job.weekday,
            service_id=job.service_id,
            team=job.team,
            off_days=off_days,
            employee_pool=employee_pool,
        ):
            legal.append(employee)
    exact = [employee for employee in legal if employee.level == job.window.level]
    if not exact:
        return False

    def sort_key(employee: Employee) -> tuple:
        remaining = employee.contractual_hours_per_week - _hours_in_week(
            assignments, employee.id, job.day_index
        )
        return (
            _versatility(draft, assignments, employee, empty_jobs, job, off_days, employee_pool),
            -remaining,
            employee.id,
        )

    ranked = sorted(exact, key=sort_key)
    best = sort_key(ranked[0])
    tied = [employee for employee in ranked if sort_key(employee) == best]
    chosen = rng.choice(tied)
    structure = draft.structure_for(job.team, job.service_id, job.weekday)
    if structure is None:
        return False
    assigned = _assigned_window(chosen, job.window, structure)
    if assigned is None:
        return False
    _append_shift(
        assignments,
        chosen,
        day_index=job.day_index,
        weekday=job.weekday,
        service_id=job.service_id,
        team=job.team,
        window=assigned,
    )
    return True


def _order_jobs(
    jobs: list[_FillWindowJob],
    rng: random.Random,
    *,
    key,
) -> list[_FillWindowJob]:
    decorated = [(key(job), rng.random(), job) for job in jobs]
    decorated.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in decorated]


def _build_seed(
    draft: PlanningDraft,
    seeder: str,
    seed_index: int,
    jobs: list[_FillWindowJob] | None = None,
    deadline: float | None = None,
) -> tuple[Shift, ...]:
    if seeder == "empty":
        return ()
    rng = _seeder_rng(seeder, seed_index)
    off_days = _forced_off_days(draft)
    pool = list(draft.employees)
    if jobs is None:
        jobs = _fill_window_jobs(draft, off_days, pool)
    assignments: list[Shift] = []

    def frozen_eligible(job: _FillWindowJob) -> int:
        return job.eligible_count

    if seeder == "tight-dynamic":
        skipped: set[tuple] = set()
        while True:
            empty = [
                job
                for job in _empty_windows(draft, assignments, jobs)
                if (
                    job.day_index,
                    job.service_id,
                    job.team,
                    job.window.level,
                    job.window.start_minutes,
                )
                not in skipped
            ]
            scored: list[tuple[int, _FillWindowJob]] = []
            for job in empty:
                count = _eligible_count_for_job(draft, assignments, job, off_days, pool)
                if 1 <= count <= SEED_TIGHT_THRESHOLD:
                    scored.append((count, job))
            if not scored:
                break
            if deadline is not None and time.perf_counter() >= deadline:
                break
            ordered = _order_jobs(
                [job for _count, job in scored],
                rng,
                key=lambda job: min(count for count, item in scored if item is job),
            )
            target = ordered[0]
            empty_now = _empty_windows(draft, assignments, jobs)
            if not _try_seed_shift(draft, assignments, target, off_days, pool, empty_now, rng):
                skipped.add(
                    (
                        target.day_index,
                        target.service_id,
                        target.team,
                        target.window.level,
                        target.window.start_minutes,
                    )
                )
        return tuple(assignments)

    if seeder == "high-role":
        candidates = list(jobs)
        ordered = _order_jobs(
            candidates,
            rng,
            key=lambda job: (-job.window.level, frozen_eligible(job)),
        )
    elif seeder == "weekend-scarce":
        candidates = [
            job
            for job in jobs
            if job.weekday in WEEKEND_WEEKDAYS and frozen_eligible(job) <= SEED_TIGHT_THRESHOLD
        ]
        ordered = _order_jobs(candidates, rng, key=frozen_eligible)
    else:
        candidates = [job for job in jobs if frozen_eligible(job) <= SEED_TIGHT_THRESHOLD]
        ordered = _order_jobs(candidates, rng, key=frozen_eligible)

    for job in ordered:
        if _window_covered(
            assignments,
            day_index=job.day_index,
            service_id=job.service_id,
            team=job.team,
            window=job.window,
            cell_windows=job.cell_windows,
        ):
            continue
        empty_now = _empty_windows(draft, assignments, jobs)
        _try_seed_shift(draft, assignments, job, off_days, pool, empty_now, rng)
    return tuple(assignments)


def _exclude_calendar(
    model: cp_model.CpModel,
    work: dict[tuple[str, int], cp_model.IntVar],
    draft: PlanningDraft,
    off_days: dict[str, set[int]],
) -> None:
    diffs = []
    for employee in draft.employees:
        rest = off_days.get(employee.id, set())
        for day in range(CYCLE_DAYS):
            if day in rest:
                diffs.append(work[employee.id, day])
            else:
                diffs.append(1 - work[employee.id, day])
    if diffs:
        model.Add(sum(diffs) >= 1)


def _first_rest_calendar(
    model: cp_model.CpModel,
    work: dict[tuple[str, int], cp_model.IntVar],
    draft: PlanningDraft,
    seconds: float,
) -> dict[str, set[int]] | None:
    collector = _collect_rest_solutions(model, work, draft, limit=1, seconds=max(0.01, seconds))
    if collector.unique_count:
        return collector.patterns[0]
    return None


def generate_cycle(draft: PlanningDraft, search: SearchEffort | None = None) -> EngineResult:
    if SEQUENTIAL_WEEK_SOLVE:
        raise RuntimeError("Sequential week-A-then-week-B generation is not used")
    effort = search if search is not None else draft.search_effort
    limit = SEARCH_CALENDAR_LIMITS[effort]
    seconds = SEARCH_SECONDS[effort]
    deadline = time.perf_counter() + seconds
    best: EngineResult | None = None
    best_key: tuple | None = None
    roster = list(draft.employees)
    SEARCH_PROGRESS["calendars"] = 0

    def consider(off_days: dict[str, set[int]], locks: tuple[Shift, ...] = ()) -> None:
        nonlocal best, best_key
        assignments = _fill_assignments(draft, off_days, roster, locks=locks)
        result = evaluate(draft.with_assignments(assignments))
        key = _attempt_key(draft, result)
        if best_key is None or key < best_key:
            best = result
            best_key = key
        SEARCH_PROGRESS["calendars"] = SEARCH_PROGRESS.get("calendars", 0) + 1

    if effort is SearchEffort.MINIMAL:
        hard, work, _unders = _build_rest_model(draft, hard_coverage=True)
        collector = _collect_rest_solutions(
            hard,
            work,
            draft,
            limit=limit,
            seconds=seconds,
            deadline=deadline,
            on_unique=consider,
            store=False,
        )
        if collector.unique_count == 0:
            consider(_slack_or_fallback(draft, max(0.01, deadline - time.perf_counter())))
        assert best is not None
        return best

    states: list[dict] = []
    seed_jobs = _fill_window_jobs(draft, _forced_off_days(draft), roster)
    for seeder, seed_index in _seed_specs(effort):
        if time.perf_counter() >= deadline:
            break
        locks = _build_seed(draft, seeder, seed_index, jobs=seed_jobs, deadline=deadline)
        remaining = max(0.01, deadline - time.perf_counter())
        model, work, _unders = _build_rest_model(draft, hard_coverage=True, locks=locks)
        first = _first_rest_calendar(model, work, draft, remaining)
        if first is None:
            if seeder == "empty":
                consider(_slack_or_fallback(draft, remaining), locks)
            continue
        states.append({"locks": locks, "model": model, "work": work, "next": first})

    produced = 0
    while states and (limit is None or produced < limit) and time.perf_counter() < deadline:
        progressed = False
        surviving: list[dict] = []
        for state in states:
            if limit is not None and produced >= limit:
                surviving.append(state)
                continue
            if time.perf_counter() >= deadline:
                surviving.append(state)
                continue
            off = state.pop("next", None)
            if off is None:
                remaining = max(0.01, deadline - time.perf_counter())
                _exclude_calendar(state["model"], state["work"], draft, state["last"])
                off = _first_rest_calendar(state["model"], state["work"], draft, remaining)
            if off is None:
                continue
            consider(off, state["locks"])
            state["last"] = off
            produced += 1
            progressed = True
            surviving.append(state)
        states = surviving
        if not progressed:
            break

    if best is None:
        consider(_slack_or_fallback(draft, max(0.01, deadline - time.perf_counter())))
    assert best is not None
    return best
