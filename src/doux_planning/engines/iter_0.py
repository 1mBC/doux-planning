"""Iterative repair post-processor (iter-0).

Starts from core-5 result, then applies repair passes to improve.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from doux_planning.coverage import derive_post_windows
from doux_planning.engine import (
    EngineResult,
    PlanningDraft,
    SearchTrace,
    Shift,
    _attempt_key,
    _hours_in_week,
    _rest_between_ok,
    _would_exceed_coupures,
    _would_exceed_max_services,
    evaluate,
    generate_cycle as core5_generate_cycle,
)
from doux_planning.types import (
    CYCLE_DAYS,
    MAX_COUPURE_HOURS,
    MAX_WEEKLY_HOURS,
    SearchEffort,
    WEEKDAYS,
)

MAX_REPAIR_ITERATIONS = 10
MAX_TOTAL_PASSES = 3


@dataclass
class RepairStats:
    surqual_swaps: int = 0
    hour_transfers: int = 0
    holes_filled: int = 0
    coupures_reduced: int = 0
    
    @property
    def total(self) -> int:
        return self.surqual_swaps + self.hour_transfers + self.holes_filled + self.coupures_reduced


def _is_legal_assignment(
    draft: PlanningDraft,
    assignments: list[Shift],
    new_shift: Shift,
    employee_id: str,
) -> bool:
    """Check if adding new_shift for employee_id would be legal."""
    employee = draft.employee(employee_id)
    
    if employee.level < new_shift.post_level:
        return False
    
    trial_list = [s for s in assignments if s.employee_id != employee_id or s != new_shift]
    trial_list.append(new_shift)
    
    if not _rest_between_ok(trial_list, new_shift):
        return False
    
    if _would_exceed_coupures(trial_list, employee, new_shift):
        return False
    
    if _would_exceed_max_services(trial_list, employee, new_shift):
        return False
    
    week_hours = _hours_in_week(trial_list, employee_id, new_shift.day_index)
    if week_hours > MAX_WEEKLY_HOURS + 1e-9:
        return False
    
    day_shifts = [
        s for s in trial_list
        if s.employee_id == employee_id and s.day_index == new_shift.day_index
    ]
    if len(day_shifts) >= 2:
        ordered = sorted(day_shifts, key=lambda s: s.start_minutes)
        for first, second in zip(ordered, ordered[1:]):
            gap = second.start_minutes - first.end_minutes
            if gap > MAX_COUPURE_HOURS * 60:
                return False
    
    return True


def _has_gap(shifts: list[Shift]) -> bool:
    """Check if there's a gap between shifts (coupure)."""
    if len(shifts) < 2:
        return False
    ordered = sorted(shifts, key=lambda s: s.start_minutes)
    return any(
        second.start_minutes - first.end_minutes > 0
        for first, second in zip(ordered, ordered[1:])
    )


def _pass_swap_surqual(
    draft: PlanningDraft,
    assignments: list[Shift],
    stats: RepairStats,
) -> bool:
    """Swap overqualified employees with better-fit ones on same day."""
    changed = False
    employees_by_id = {e.id: e for e in draft.employees}
    
    for i, shift in enumerate(assignments):
        employee = employees_by_id.get(shift.employee_id)
        if employee is None:
            continue
        
        surqual = employee.level - shift.post_level
        if surqual < 2:
            continue
        
        same_day_shifts = [
            (j, s) for j, s in enumerate(assignments)
            if s.day_index == shift.day_index
            and s.employee_id != shift.employee_id
            and s.team == shift.team
            and j != i
        ]
        
        for j, other_shift in same_day_shifts:
            other_employee = employees_by_id.get(other_shift.employee_id)
            if other_employee is None:
                continue
            
            if other_employee.level < shift.post_level:
                continue
            
            other_surqual = other_employee.level - other_shift.post_level
            if other_surqual >= surqual:
                continue
            
            new_shift_for_other = replace(
                shift,
                employee_id=other_employee.id,
            )
            new_shift_for_current = replace(
                other_shift,
                employee_id=employee.id,
            )
            
            if employee.level < other_shift.post_level:
                continue
            
            test_assignments = list(assignments)
            test_assignments[i] = new_shift_for_other
            test_assignments[j] = new_shift_for_current
            
            if not _is_legal_assignment(draft, test_assignments, new_shift_for_other, other_employee.id):
                continue
            if not _is_legal_assignment(draft, test_assignments, new_shift_for_current, employee.id):
                continue
            
            assignments[i] = new_shift_for_other
            assignments[j] = new_shift_for_current
            stats.surqual_swaps += 1
            changed = True
            break
        
        if changed:
            break
    
    return changed


def _pass_balance_hours(
    draft: PlanningDraft,
    assignments: list[Shift],
    stats: RepairStats,
) -> bool:
    """Transfer shifts to balance hours closer to contracts."""
    changed = False
    employees = list(draft.employees)
    
    for e1 in employees:
        hours1 = sum(
            s.duration_hours for s in assignments if s.employee_id == e1.id
        )
        gap1 = hours1 - e1.contractual_hours_per_week
        
        if abs(gap1) <= 2:
            continue
        
        for e2 in employees:
            if e2.id == e1.id or e2.team != e1.team:
                continue
            
            hours2 = sum(
                s.duration_hours for s in assignments if s.employee_id == e2.id
            )
            gap2 = hours2 - e2.contractual_hours_per_week
            
            if abs(gap2) <= 2:
                continue
            
            if (gap1 > 0 and gap2 > 0) or (gap1 < 0 and gap2 < 0):
                continue
            
            if gap1 > 0:
                over, under = e1, e2
            else:
                over, under = e2, e1
            
            for i, shift in enumerate(assignments):
                if shift.employee_id != over.id:
                    continue
                
                if under.level < shift.post_level:
                    continue
                
                new_shift = replace(shift, employee_id=under.id)
                
                test_assignments = [s for s in assignments if s != shift]
                test_assignments.append(new_shift)
                
                if not _is_legal_assignment(draft, test_assignments, new_shift, under.id):
                    continue
                
                assignments[i] = new_shift
                stats.hour_transfers += 1
                changed = True
                break
            
            if changed:
                break
        
        if changed:
            break
    
    return changed


def _pass_fill_holes(
    draft: PlanningDraft,
    assignments: list[Shift],
    stats: RepairStats,
) -> bool:
    """Try to fill empty posts with the updated grid."""
    changed = False
    employees_by_team = {}
    for e in draft.employees:
        employees_by_team.setdefault(e.team, []).append(e)
    
    for d in range(CYCLE_DAYS):
        weekday = WEEKDAYS[d % 7]
        for s_id in draft.hours.services:
            if draft.hours.is_closed(weekday, s_id):
                continue
            
            for team, team_employees in employees_by_team.items():
                structure = draft.structure_for(team, s_id, weekday)
                if structure is None:
                    continue
                
                windows = derive_post_windows(structure)
                covered_levels = set()
                for shift in assignments:
                    if shift.day_index == d and shift.service_id == s_id and shift.team == team:
                        covered_levels.add(shift.post_level)
                
                for window in windows:
                    if window.level in covered_levels:
                        continue
                    
                    for employee in sorted(team_employees, key=lambda e: e.level):
                        if employee.level < window.level:
                            continue
                        
                        already_on_service = any(
                            s.employee_id == employee.id
                            and s.day_index == d
                            and s.service_id == s_id
                            for s in assignments
                        )
                        if already_on_service:
                            continue
                        
                        new_shift = Shift(
                            employee_id=employee.id,
                            day_index=d,
                            weekday=weekday,
                            service_id=s_id,
                            team=team,
                            start_minutes=window.start_minutes,
                            end_minutes=window.end_minutes,
                            post_level=window.level,
                        )
                        
                        if not _is_legal_assignment(draft, assignments, new_shift, employee.id):
                            continue
                        
                        assignments.append(new_shift)
                        covered_levels.add(window.level)
                        stats.holes_filled += 1
                        changed = True
                        break
    
    return changed


def _pass_reduce_coupures(
    draft: PlanningDraft,
    assignments: list[Shift],
    stats: RepairStats,
) -> bool:
    """Reduce coupures by swapping shifts away from small contracts."""
    changed = False
    employees_by_id = {e.id: e for e in draft.employees}
    
    employees_with_coupures = []
    for e in draft.employees:
        for d in range(CYCLE_DAYS):
            day_shifts = [
                s for s in assignments
                if s.employee_id == e.id and s.day_index == d
            ]
            if _has_gap(day_shifts):
                employees_with_coupures.append((e, d, day_shifts))
    
    employees_with_coupures.sort(key=lambda x: x[0].contractual_hours_per_week)
    
    for employee, day, day_shifts in employees_with_coupures:
        for shift in day_shifts:
            same_day_others = [
                e for e in draft.employees
                if e.id != employee.id and e.team == employee.team
            ]
            
            for other in same_day_others:
                if other.level < shift.post_level:
                    continue
                
                other_day_shifts = [
                    s for s in assignments
                    if s.employee_id == other.id and s.day_index == day
                ]
                
                test_shifts = other_day_shifts + [shift]
                if _has_gap(test_shifts):
                    continue
                
                new_shift = replace(shift, employee_id=other.id)
                
                test_assignments = [s for s in assignments if s != shift]
                test_assignments.append(new_shift)
                
                if not _is_legal_assignment(draft, test_assignments, new_shift, other.id):
                    continue
                
                idx = assignments.index(shift)
                assignments[idx] = new_shift
                stats.coupures_reduced += 1
                changed = True
                break
            
            if changed:
                break
        
        if changed:
            break
    
    return changed


def _repair_loop(
    draft: PlanningDraft,
    assignments: list[Shift],
    max_passes: int = MAX_TOTAL_PASSES,
) -> tuple[list[Shift], RepairStats]:
    """Run repair passes until convergence or max iterations."""
    stats = RepairStats()
    
    for _ in range(max_passes):
        changed = False
        
        for _ in range(MAX_REPAIR_ITERATIONS):
            if _pass_swap_surqual(draft, assignments, stats):
                changed = True
                break
        
        for _ in range(MAX_REPAIR_ITERATIONS):
            if _pass_balance_hours(draft, assignments, stats):
                changed = True
                break
        
        for _ in range(MAX_REPAIR_ITERATIONS):
            if _pass_fill_holes(draft, assignments, stats):
                changed = True
                break
        
        for _ in range(MAX_REPAIR_ITERATIONS):
            if _pass_reduce_coupures(draft, assignments, stats):
                changed = True
                break
        
        if not changed:
            break
    
    return assignments, stats


def generate_cycle(
    draft: PlanningDraft, search: SearchEffort | None = None
) -> EngineResult:
    """Generate planning using core-5 + iterative repair."""
    base_result = core5_generate_cycle(draft, search)
    
    base_key = _attempt_key(draft, base_result)
    
    assignments = list(base_result.assignments)
    repaired_assignments, stats = _repair_loop(draft, assignments)
    
    repaired_result = evaluate(draft.with_assignments(tuple(repaired_assignments)))
    repaired_key = _attempt_key(draft, repaired_result)
    
    if repaired_key <= base_key:
        final_result = repaired_result
        final_key = repaired_key
        final_assignments = tuple(repaired_assignments)
    else:
        final_result = base_result
        final_key = base_key
        final_assignments = base_result.assignments
    
    empty, interdit, hours_miss, souhait, below_role, overqual = final_key
    
    trace = SearchTrace(
        seeder="iter",
        seed_index=0,
        n_locks=0,
        calendars_by_seeder={"iter": 1},
        calendars_total=1,
        seeds_infeasible=0,
        attempt_key={
            "empty": empty,
            "interdit": interdit,
            "hours_miss": hours_miss,
            "souhait": souhait,
            "below_role": below_role,
            "overqual": overqual,
            "base_engine": "core-5",
            "iterations": stats.total,
            "improvements": {
                "surqual_swaps": stats.surqual_swaps,
                "hour_transfers": stats.hour_transfers,
                "holes_filled": stats.holes_filled,
                "coupures_reduced": stats.coupures_reduced,
            },
        },
    )
    
    return EngineResult(
        assignments=final_assignments,
        warnings=final_result.warnings,
        trace=trace,
    )
