from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from doux_planning.engine import EngineResult, PlanningDraft, Shift, evaluate, generate_cycle, publish_allowed
from doux_planning.invites import EmployeeAccount, RestaurantIdentity
from doux_planning.staff import Employee, Unavailability, default_legal_rules
from doux_planning.structures import RestaurantHours, ServiceStructure, StructuralEditRequiresCycleSandbox
from doux_planning.types import WEEKDAYS
from doux_planning.warnings import Warning


@dataclass(frozen=True)
class Intent:
    kind: str
    employee_id: str
    weekday: str | None = None
    day_index: int | None = None
    service_id: str | None = None
    force_shift: Shift | None = None


@dataclass
class CalendarWeek:
    week_id: str
    week_start: date
    cycle_id: str
    intents: list[Intent] = field(default_factory=list)
    assignments: tuple[Shift, ...] = ()
    warnings: tuple[Warning, ...] = ()

    @property
    def is_dirty(self) -> bool:
        return bool(self.intents)


@dataclass
class PublishedCycle:
    id: str
    draft: PlanningDraft
    result: EngineResult


@dataclass
class Sandbox:
    restaurant_id: str
    target: str
    week_id: str | None
    draft: PlanningDraft
    last_result: EngineResult | None = None
    intents: list[Intent] = field(default_factory=list)


@dataclass(frozen=True)
class Reconciliation:
    week_id: str
    proposal: EngineResult
    options: tuple[str, ...] = ("accept", "keep", "open-in-sandbox")


@dataclass
class RestaurantState:
    identity: RestaurantIdentity
    employees: list[Employee]
    structures: list[ServiceStructure]
    hours: RestaurantHours
    cycle: PublishedCycle | None = None
    weeks: dict[str, CalendarWeek] = field(default_factory=dict)
    sandbox: Sandbox | None = None
    accounts: list[EmployeeAccount] = field(default_factory=list)
    today: date = field(default_factory=date.today)

    def as_draft(self, assignments: tuple[Shift, ...] = ()) -> PlanningDraft:
        return PlanningDraft(
            employees=tuple(self.employees),
            structures=tuple(self.structures),
            hours=self.hours,
            assignments=assignments,
            legal_rules=default_legal_rules(),
        )


class PlanningStore:
    def __init__(self) -> None:
        self._restaurants: dict[str, RestaurantState] = {}

    def add_restaurant(self, state: RestaurantState) -> None:
        self._restaurants[state.identity.id] = state

    def get(self, restaurant_id: str) -> RestaurantState:
        return self._restaurants[restaurant_id]

    def enter_sandbox(self, restaurant_id: str, target: str, week_id: str | None = None) -> Sandbox:
        state = self.get(restaurant_id)
        if state.sandbox is not None:
            return state.sandbox
        if target not in {"cycle", "week"}:
            raise ValueError("Sandbox target must be cycle or week")
        if target == "week" and not week_id:
            raise ValueError("Week sandbox requires week_id")
        if target == "cycle":
            draft = state.cycle.draft if state.cycle else state.as_draft()
            intents: list[Intent] = []
        else:
            week = state.weeks[week_id]
            draft = state.as_draft(week.assignments)
            intents = list(week.intents)
        sandbox = Sandbox(
            restaurant_id=restaurant_id,
            target=target,
            week_id=week_id,
            draft=draft,
            last_result=evaluate(draft),
            intents=intents,
        )
        state.sandbox = sandbox
        return sandbox

    def edit_structure(self, restaurant_id: str, structures: list[ServiceStructure] | tuple[ServiceStructure, ...]) -> Sandbox:
        sandbox = self.get(restaurant_id).sandbox
        if sandbox is None or sandbox.target != "cycle":
            raise StructuralEditRequiresCycleSandbox("Structural config uses the cycle sandbox")
        sandbox.draft = replace(sandbox.draft, structures=tuple(structures))
        sandbox.last_result = evaluate(sandbox.draft)
        return sandbox

    def apply_edit(self, restaurant_id: str, assignments: tuple[Shift, ...]) -> EngineResult:
        sandbox = self.get(restaurant_id).sandbox
        if sandbox is None:
            raise RuntimeError("No sandbox")
        sandbox.draft = sandbox.draft.with_assignments(assignments)
        sandbox.last_result = evaluate(sandbox.draft)
        return sandbox.last_result

    def discard_sandbox(self, restaurant_id: str) -> None:
        self.get(restaurant_id).sandbox = None

    def publish_sandbox(self, restaurant_id: str, acknowledged: set[tuple] | frozenset[tuple] | None = None) -> list[Reconciliation]:
        state = self.get(restaurant_id)
        sandbox = state.sandbox
        if sandbox is None:
            raise RuntimeError("No sandbox")
        result = sandbox.last_result or evaluate(sandbox.draft)
        acked = frozenset(acknowledged or ())
        if not publish_allowed(result, acked):
            raise PermissionError("Acknowledge interdit warnings before publish")
        if sandbox.target == "week":
            week = state.weeks[sandbox.week_id]
            week.assignments = result.assignments
            week.warnings = result.warnings
            week.intents = list(sandbox.intents)
            state.sandbox = None
            return []
        return self._publish_cycle(state, sandbox.draft, result)

    def _publish_cycle(
        self, state: RestaurantState, draft: PlanningDraft, result: EngineResult
    ) -> list[Reconciliation]:
        cycle_id = state.cycle.id if state.cycle else "cycle-1"
        if state.cycle:
            cycle_id = state.cycle.id
        state.cycle = PublishedCycle(id=cycle_id, draft=draft.with_assignments(result.assignments), result=result)
        state.hours = draft.hours
        state.structures = list(draft.structures)
        reconciliations: list[Reconciliation] = []
        for week in state.weeks.values():
            week_end = week.week_start + timedelta(days=6)
            if week_end < state.today:
                continue
            if week.is_dirty:
                proposal = _replay_intents(state.cycle.draft, week)
                reconciliations.append(Reconciliation(week_id=week.week_id, proposal=proposal))
                continue
            projected = _project_cycle_week(state.cycle.result.assignments, week.week_start)
            week.cycle_id = state.cycle.id
            week.assignments = _keep_elapsed_days(
                week.assignments, projected, week.week_start, state.today
            )
            week.warnings = ()
        state.sandbox = None
        return reconciliations

    def accept_reconciliation(self, restaurant_id: str, week_id: str, proposal: EngineResult) -> None:
        week = self.get(restaurant_id).weeks[week_id]
        week.assignments = proposal.assignments
        week.warnings = proposal.warnings

    def keep_week(self, restaurant_id: str, week_id: str) -> None:
        _ = (restaurant_id, week_id)

    def record_unavailability(self, restaurant_id: str, employee_id: str, weekday: str) -> EngineResult:
        state = self.get(restaurant_id)
        sandbox = state.sandbox
        if sandbox is None:
            raise RuntimeError("No sandbox")
        sandbox.intents.append(Intent(kind="unavailability", employee_id=employee_id, weekday=weekday))
        remaining = tuple(
            shift
            for shift in sandbox.draft.assignments
            if not (shift.employee_id == employee_id and shift.weekday == weekday)
        )
        return self.apply_edit(restaurant_id, remaining)

    def employee_view(self, restaurant_id: str, account: EmployeeAccount) -> tuple[Shift, ...]:
        state = self.get(restaurant_id)
        if account.restaurant_id != restaurant_id:
            return ()
        published: list[Shift] = []
        if state.weeks:
            for week in state.weeks.values():
                published.extend(week.assignments)
        elif state.cycle:
            published.extend(state.cycle.result.assignments)
        return tuple(shift for shift in published if shift.employee_id == account.employee_id)

    def generate_into_sandbox(self, restaurant_id: str) -> EngineResult:
        sandbox = self.get(restaurant_id).sandbox
        if sandbox is None or sandbox.target != "cycle":
            raise StructuralEditRequiresCycleSandbox("Generation writes the cycle sandbox")
        result = generate_cycle(sandbox.draft)
        sandbox.draft = sandbox.draft.with_assignments(result.assignments)
        sandbox.last_result = result
        return result


def instantiate_week(cycle_assignments: tuple[Shift, ...], week_start: date, week_id: str, cycle_id: str) -> CalendarWeek:
    return CalendarWeek(
        week_id=week_id,
        week_start=week_start,
        cycle_id=cycle_id,
        assignments=_project_cycle_week(cycle_assignments, week_start),
    )


def _project_cycle_week(cycle_assignments: tuple[Shift, ...], week_start: date) -> tuple[Shift, ...]:
    base = 0 if week_start.isocalendar().week % 2 == 1 else 7
    selected = [
        shift for shift in cycle_assignments if base <= shift.day_index < base + 7
    ]
    if not selected:
        selected = [shift for shift in cycle_assignments if 0 <= shift.day_index < 7]
        base = 0
    projected = []
    for shift in selected:
            offset = shift.day_index - base
            projected.append(
                replace(
                    shift,
                    day_index=offset,
                    weekday=WEEKDAYS[offset],
                )
            )
    return tuple(projected)


def _keep_elapsed_days(
    old: tuple[Shift, ...],
    new: tuple[Shift, ...],
    week_start: date,
    today: date,
) -> tuple[Shift, ...]:
    if week_start >= today:
        return new
    kept = [shift for shift in old if week_start + timedelta(days=shift.day_index) < today]
    incoming = [shift for shift in new if week_start + timedelta(days=shift.day_index) >= today]
    return tuple(kept + incoming)


def _replay_intents(cycle_draft: PlanningDraft, week: CalendarWeek) -> EngineResult:
    projected = _project_cycle_week(cycle_draft.assignments, week.week_start)
    employees = []
    for employee in cycle_draft.employees:
        extra = []
        for intent in week.intents:
            if intent.kind == "unavailability" and intent.employee_id == employee.id:
                extra.append(Unavailability(weekday=intent.weekday))
        if extra:
            employees.append(replace(employee, unavailabilities=employee.unavailabilities + tuple(extra)))
        else:
            employees.append(employee)
    draft = replace(
        cycle_draft,
        employees=tuple(employees),
        assignments=tuple(
            shift
            for shift in projected
            if not any(
                intent.kind == "unavailability"
                and intent.employee_id == shift.employee_id
                and intent.weekday == shift.weekday
                for intent in week.intents
            )
        ),
        horizon_days=7,
    )
    forced = [
        intent.force_shift
        for intent in week.intents
        if intent.kind == "forced_assignment" and intent.force_shift is not None
    ]
    if forced:
        draft = draft.with_assignments(draft.assignments + tuple(forced))
    return evaluate(draft)
