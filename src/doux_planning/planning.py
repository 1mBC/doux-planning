from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from doux_planning.engine import (
    EngineResult,
    PlanningDraft,
    Shift,
    _attempt_key,
    _hours_miss,
    evaluate,
    generate_cycle,
    publish_allowed,
    rank_candidates,
    swap_shifts,
)
from doux_planning.invites import EmployeeAccount, RestaurantIdentity
from doux_planning.staff import Employee, RoleLadder, Unavailability, default_legal_rules
from doux_planning.structures import (
    RestaurantHours,
    ServiceStructure,
    ServiceType,
    StructuralEditRequiresCycleSandbox,
    TypicalWeek,
)
from doux_planning.types import WEEKDAYS, Team, WarningSeverity, validate_quantum
from doux_planning.warnings import Warning

DAY_END_MINUTES = 24 * 60
CONTRACT_HOUR_TOLERANCE = 0.5


class EmptyHistoryError(RuntimeError):
    pass


class IdentityRetuneError(ValueError):
    pass


class OccupiedSlotError(ValueError):
    pass


@dataclass(frozen=True)
class FillSlot:
    employee_id: str
    day_index: int
    weekday: str
    service_id: str
    team: Team


@dataclass(frozen=True)
class WarningDelta:
    added: tuple[Warning, ...]
    removed: tuple[Warning, ...]
    unchanged: tuple[Warning, ...]


@dataclass(frozen=True)
class ContractImpact:
    employee_id: str
    week_start: int
    current_hours: float
    trial_hours: float
    contracted: float
    kind: str


@dataclass(frozen=True)
class RoleFitImpact:
    current_gap: int
    trial_gap: int
    kind: str


@dataclass(frozen=True)
class PreviewImpact:
    new_interdits: tuple[Warning, ...]
    broken_wishes: tuple[Warning, ...]
    contract: tuple[ContractImpact, ...]
    coverage_added: tuple[Warning, ...]
    coverage_removed: tuple[Warning, ...]
    role_fit: tuple[RoleFitImpact, ...]


@dataclass(frozen=True)
class PreviewProposal:
    rank: int
    gesture: str
    result: EngineResult
    delta: WarningDelta
    impact: PreviewImpact
    current_score: tuple
    trial_score: tuple
    start_minutes: int | None = None
    end_minutes: int | None = None
    employee_id: str | None = None
    partner: Shift | None = None


@dataclass(frozen=True)
class SandboxSnapshot:
    assignments: tuple[Shift, ...]
    last_result: EngineResult | None


def warning_identity(warning: Warning) -> tuple:
    return (warning.severity.value, warning.code, warning.employee_id, warning.day_index)


def warning_delta(current: tuple[Warning, ...], trial: tuple[Warning, ...]) -> WarningDelta:
    current_by_id = {warning_identity(item): item for item in current}
    trial_by_id = {warning_identity(item): item for item in trial}
    added = tuple(trial_by_id[key] for key in trial_by_id if key not in current_by_id)
    removed = tuple(current_by_id[key] for key in current_by_id if key not in trial_by_id)
    unchanged = tuple(trial_by_id[key] for key in trial_by_id if key in current_by_id)
    return WarningDelta(added=added, removed=removed, unchanged=unchanged)


def _clip_minutes(value: int) -> int:
    return max(0, min(DAY_END_MINUTES, value))


def _fill_hours(
    draft: PlanningDraft,
    slot: FillSlot,
    row: Employee,
    start_minutes: int | None,
    end_minutes: int | None,
) -> tuple[int, int]:
    if draft.hours.is_closed(slot.weekday, slot.service_id):
        raise ValueError("Service is closed")
    if start_minutes is None and end_minutes is None:
        structure = draft.structure_for(slot.team, slot.service_id, slot.weekday)
        if structure is None:
            raise ValueError("Service is closed")
        start = min(wave.time_minutes for wave in structure.arrivals)
        end = max(wave.time_minutes for wave in structure.departures)
    elif start_minutes is None or end_minutes is None:
        raise ValueError("Fill hours must both be omitted or both set")
    else:
        start = validate_quantum(_clip_minutes(start_minutes))
        end = validate_quantum(_clip_minutes(end_minutes))
    if start >= end or end - start < int(row.min_shift_hours * 60):
        raise ValueError("Fill duration is below min_shift_hours")
    return start, end


def _week_hours(assignments: tuple[Shift, ...] | list[Shift], employee_id: str, week_start: int) -> float:
    return round(
        sum(
            shift.duration_hours
            for shift in assignments
            if shift.employee_id == employee_id and week_start <= shift.day_index < week_start + 7
        ),
        2,
    )


def _contract_kind(current_hours: float, trial_hours: float, contracted: float) -> str | None:
    if abs(trial_hours - current_hours) < 1e-9:
        return None
    if trial_hours > contracted + CONTRACT_HOUR_TOLERANCE:
        return "excess"
    current_gap = abs(current_hours - contracted)
    trial_gap = abs(trial_hours - contracted)
    if trial_gap + 1e-9 < current_gap:
        return "closer"
    if trial_gap > current_gap + 1e-9:
        return "farther"
    return None


def _post_key(shift: Shift) -> tuple:
    return (
        shift.day_index,
        shift.weekday,
        shift.service_id,
        shift.team,
        shift.start_minutes,
        shift.end_minutes,
        shift.post_level,
    )


def _slot_on_post(assignments: tuple[Shift, ...] | list[Shift], slot: Shift) -> Shift | None:
    matches = [item for item in assignments if _post_key(item) == _post_key(slot)]
    if len(matches) != 1:
        return None
    return matches[0]


def _role_gap(draft: PlanningDraft, shift: Shift) -> int | None:
    person = next((item for item in draft.employees if item.id == shift.employee_id), None)
    if person is None:
        return None
    return person.level - shift.post_level


def _role_fit(
    draft: PlanningDraft,
    current_slots: tuple[Shift, ...],
    trial_slots: tuple[Shift, ...],
) -> tuple[RoleFitImpact, ...]:
    if not current_slots or len(current_slots) != len(trial_slots):
        return ()
    current_gaps = [_role_gap(draft, slot) for slot in current_slots]
    trial_gaps = [_role_gap(draft, slot) for slot in trial_slots]
    if any(gap is None for gap in (*current_gaps, *trial_gaps)):
        return ()
    current_gap = sum(current_gaps)
    trial_gap = sum(trial_gaps)
    if trial_gap < current_gap:
        kind = "better"
    elif trial_gap > current_gap:
        kind = "worse"
    else:
        return ()
    return (RoleFitImpact(current_gap=current_gap, trial_gap=trial_gap, kind=kind),)


def preview_impact(
    draft: PlanningDraft,
    current: EngineResult,
    trial: EngineResult,
    employee_ids: set[str],
    current_slots: tuple[Shift, ...] = (),
    trial_slots: tuple[Shift, ...] = (),
) -> PreviewImpact:
    delta = warning_delta(current.warnings, trial.warnings)
    contracts: list[ContractImpact] = []
    by_id = {employee.id: employee for employee in draft.employees}
    for employee_id in sorted(employee_ids):
        person = by_id.get(employee_id)
        if person is None:
            continue
        for week_start in (0, 7):
            current_hours = _week_hours(current.assignments, employee_id, week_start)
            trial_hours = _week_hours(trial.assignments, employee_id, week_start)
            kind = _contract_kind(current_hours, trial_hours, person.contractual_hours_per_week)
            if kind is None:
                continue
            contracts.append(
                ContractImpact(
                    employee_id=employee_id,
                    week_start=week_start,
                    current_hours=current_hours,
                    trial_hours=trial_hours,
                    contracted=person.contractual_hours_per_week,
                    kind=kind,
                )
            )
    return PreviewImpact(
        new_interdits=tuple(item for item in delta.added if item.severity == WarningSeverity.INTERDIT),
        broken_wishes=tuple(
            item
            for item in delta.added
            if item.severity == WarningSeverity.SOUHAIT and item.code != "contract_hours"
        ),
        contract=tuple(contracts),
        coverage_added=tuple(item for item in delta.added if item.code == "empty_post"),
        coverage_removed=tuple(item for item in delta.removed if item.code == "empty_post"),
        role_fit=_role_fit(draft, current_slots, trial_slots),
    )


def occupied_sort_key(draft: PlanningDraft, current: EngineResult, trial: EngineResult) -> tuple:
    delta = warning_delta(current.warnings, trial.warnings)
    added_interdit = sum(1 for item in delta.added if item.severity == WarningSeverity.INTERDIT)
    added_souhait = sum(1 for item in delta.added if item.severity == WarningSeverity.SOUHAIT)
    miss_delta = _hours_miss(draft, trial.assignments) - _hours_miss(draft, current.assignments)
    return (added_interdit, added_souhait, miss_delta, _attempt_key(draft, trial))


def _make_proposal(
    *,
    rank: int,
    gesture: str,
    draft: PlanningDraft,
    current: EngineResult,
    trial: EngineResult,
    employee_ids: set[str],
    current_slots: tuple[Shift, ...],
    trial_slots: tuple[Shift, ...],
    start_minutes: int | None = None,
    end_minutes: int | None = None,
    employee_id: str | None = None,
    partner: Shift | None = None,
) -> PreviewProposal:
    delta = warning_delta(current.warnings, trial.warnings)
    return PreviewProposal(
        rank=rank,
        gesture=gesture,
        result=trial,
        delta=delta,
        impact=preview_impact(draft, current, trial, employee_ids, current_slots, trial_slots),
        current_score=_attempt_key(draft, current),
        trial_score=_attempt_key(draft, trial),
        start_minutes=start_minutes,
        end_minutes=end_minutes,
        employee_id=employee_id,
        partner=partner,
    )


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
    history: list[SandboxSnapshot] = field(default_factory=list)


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
    hours: RestaurantHours | None = None
    cycle: PublishedCycle | None = None
    weeks: dict[str, CalendarWeek] = field(default_factory=dict)
    sandbox: Sandbox | None = None
    accounts: list[EmployeeAccount] = field(default_factory=list)
    today: date = field(default_factory=date.today)
    service_types: list[ServiceType] = field(default_factory=list)
    typical_week: TypicalWeek | None = None
    ladders: dict[Team, RoleLadder] = field(default_factory=dict)
    company_services: tuple[str, ...] = ()

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

    def preview_retune(
        self, restaurant_id: str, shift: Shift, start_minutes: int, end_minutes: int
    ) -> list[PreviewProposal]:
        sandbox = self._require_sandbox(restaurant_id)
        self._require_shift(sandbox, shift)
        current = sandbox.last_result or evaluate(sandbox.draft)
        start = validate_quantum(_clip_minutes(start_minutes))
        end = validate_quantum(_clip_minutes(end_minutes))
        if start == shift.start_minutes and end == shift.end_minutes:
            raise IdentityRetuneError("Retune times match the current shift")
        employee = sandbox.draft.employee(shift.employee_id)
        min_minutes = int(employee.min_shift_hours * 60)
        if start >= end or end - start < min_minutes:
            raise ValueError("Retune duration is below min_shift_hours")
        trial_shift = replace(shift, start_minutes=start, end_minutes=end)
        assignments = tuple(trial_shift if item == shift else item for item in sandbox.draft.assignments)
        trial = evaluate(sandbox.draft.with_assignments(assignments))
        return [
            _make_proposal(
                rank=1,
                gesture="retune",
                draft=sandbox.draft,
                current=current,
                trial=trial,
                employee_ids={shift.employee_id},
                current_slots=(shift,),
                trial_slots=(trial_shift,),
                start_minutes=start,
                end_minutes=end,
                employee_id=shift.employee_id,
            )
        ]

    def preview_replace(self, restaurant_id: str, shift: Shift) -> list[PreviewProposal]:
        sandbox = self._require_sandbox(restaurant_id)
        self._require_shift(sandbox, shift)
        current = sandbox.last_result or evaluate(sandbox.draft)
        remaining = tuple(item for item in sandbox.draft.assignments if item != shift)
        ranked = rank_candidates(
            sandbox.draft.with_assignments(remaining),
            shift.day_index,
            shift.weekday,
            shift.service_id,
            shift.team,
            shift.start_minutes,
            shift.end_minutes,
            shift.post_level,
        )
        ranked = [item for item in ranked if item.employee.id != shift.employee_id]
        ranked.sort(key=lambda item: occupied_sort_key(sandbox.draft, current, item.result))
        proposals: list[PreviewProposal] = []
        for index, candidate in enumerate(ranked, start=1):
            trial_slot = _slot_on_post(candidate.result.assignments, shift)
            proposals.append(
                _make_proposal(
                    rank=index,
                    gesture="replace",
                    draft=sandbox.draft,
                    current=current,
                    trial=candidate.result,
                    employee_ids={shift.employee_id, candidate.employee.id},
                    current_slots=(shift,),
                    trial_slots=() if trial_slot is None else (trial_slot,),
                    start_minutes=shift.start_minutes,
                    end_minutes=shift.end_minutes,
                    employee_id=candidate.employee.id,
                )
            )
        return proposals

    def preview_swap(self, restaurant_id: str, shift: Shift) -> list[PreviewProposal]:
        sandbox = self._require_sandbox(restaurant_id)
        self._require_shift(sandbox, shift)
        current = sandbox.last_result or evaluate(sandbox.draft)
        scored: list[tuple[Shift, EngineResult]] = []
        for partner in sandbox.draft.assignments:
            if partner == shift or partner.employee_id == shift.employee_id:
                continue
            scored.append((partner, swap_shifts(sandbox.draft, shift, partner)))
        scored.sort(
            key=lambda item: (
                occupied_sort_key(sandbox.draft, current, item[1]),
                item[0].day_index,
                item[0].service_id,
                item[0].employee_id,
                item[0].start_minutes,
            )
        )
        proposals: list[PreviewProposal] = []
        for index, (partner, result) in enumerate(scored, start=1):
            trial_slot = _slot_on_post(result.assignments, shift)
            proposals.append(
                _make_proposal(
                    rank=index,
                    gesture="swap",
                    draft=sandbox.draft,
                    current=current,
                    trial=result,
                    employee_ids={shift.employee_id, partner.employee_id},
                    current_slots=(shift,),
                    trial_slots=() if trial_slot is None else (trial_slot,),
                    employee_id=partner.employee_id,
                    partner=partner,
                )
            )
        return proposals

    def preview_fill(
        self,
        restaurant_id: str,
        slot: FillSlot,
        start_minutes: int | None = None,
        end_minutes: int | None = None,
    ) -> list[PreviewProposal]:
        sandbox = self._require_sandbox(restaurant_id)
        row = sandbox.draft.employee(slot.employee_id)
        if any(
            item.employee_id == slot.employee_id
            and item.day_index == slot.day_index
            and item.service_id == slot.service_id
            for item in sandbox.draft.assignments
        ):
            raise OccupiedSlotError("Row cell is already occupied")
        start, end = _fill_hours(sandbox.draft, slot, row, start_minutes, end_minutes)
        post_level = row.level
        current = sandbox.last_result or evaluate(sandbox.draft)
        overlapping = {
            item.employee_id
            for item in sandbox.draft.assignments
            if item.day_index == slot.day_index
            and item.start_minutes < end
            and start < item.end_minutes
        }
        duration = end - start
        scored: list[tuple[Employee, EngineResult, Shift]] = []
        for person in sandbox.draft.employees:
            if person.team != slot.team or person.level < post_level:
                continue
            if person.id in overlapping:
                continue
            if duration < int(person.min_shift_hours * 60):
                continue
            trial_shift = Shift(
                employee_id=person.id,
                day_index=slot.day_index,
                weekday=slot.weekday,
                service_id=slot.service_id,
                team=slot.team,
                start_minutes=start,
                end_minutes=end,
                post_level=post_level,
            )
            trial = evaluate(sandbox.draft.with_assignments((*sandbox.draft.assignments, trial_shift)))
            scored.append((person, trial, trial_shift))
        row_trials = [item for item in scored if item[0].id == slot.employee_id]
        others = [item for item in scored if item[0].id != slot.employee_id]
        others.sort(key=lambda item: occupied_sort_key(sandbox.draft, current, item[1]))
        ordered = row_trials + others
        return [
            _make_proposal(
                rank=index,
                gesture="fill",
                draft=sandbox.draft,
                current=current,
                trial=trial,
                employee_ids={person.id},
                current_slots=(),
                trial_slots=(),
                start_minutes=start,
                end_minutes=end,
                employee_id=person.id,
            )
            for index, (person, trial, _trial_shift) in enumerate(ordered, start=1)
        ]

    def apply_proposal(self, restaurant_id: str, proposal: PreviewProposal) -> EngineResult:
        sandbox = self._require_sandbox(restaurant_id)
        sandbox.history.append(
            SandboxSnapshot(assignments=sandbox.draft.assignments, last_result=sandbox.last_result)
        )
        return self.apply_edit(restaurant_id, proposal.result.assignments)

    def undo_sandbox(self, restaurant_id: str) -> EngineResult:
        sandbox = self._require_sandbox(restaurant_id)
        if not sandbox.history:
            raise EmptyHistoryError("No cranted sandbox edit to undo")
        snapshot = sandbox.history.pop()
        sandbox.draft = sandbox.draft.with_assignments(snapshot.assignments)
        sandbox.last_result = snapshot.last_result
        return sandbox.last_result or evaluate(sandbox.draft)

    def _require_sandbox(self, restaurant_id: str) -> Sandbox:
        sandbox = self.get(restaurant_id).sandbox
        if sandbox is None:
            raise RuntimeError("No sandbox")
        return sandbox

    def _require_shift(self, sandbox: Sandbox, shift: Shift) -> None:
        if shift not in sandbox.draft.assignments:
            raise ValueError("Shift is not in the sandbox draft")

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
