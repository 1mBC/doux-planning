"""CP-SAT global solver (cp-0).

A single CP-SAT model with all constraints, not just rest days.
Uses OR-Tools to find an optimal assignment.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from ortools.sat.python import cp_model

from doux_planning.coverage import derive_post_windows
from doux_planning.engine import (
    EngineResult,
    PlanningDraft,
    SearchTrace,
    Shift,
    _attempt_key,
    evaluate,
)
from doux_planning.types import (
    CYCLE_DAYS,
    MAX_COUPURE_HOURS,
    MAX_WEEKLY_HOURS,
    MIN_REST_BETWEEN_DAYS_HOURS,
    SearchEffort,
    ServiceName,
    Team,
    WEEKDAYS,
)

SEARCH_SECONDS = {
    SearchEffort.MINIMAL: 3.0,
    SearchEffort.OPTIMIZED: 30.0,
    SearchEffort.MAXIMAL: 600.0,
}

W_EMPTY = 1000
W_HOURS = 10
W_WISH = 50
W_BELOW = 5
W_OVERQ = 1


@dataclass
class CpTrace:
    solver_status: str
    objective_value: int | None
    solve_time_ms: int


def generate_cycle(
    draft: PlanningDraft, search: SearchEffort | None = None
) -> EngineResult:
    """Generate a planning using a single CP-SAT model."""
    effort = search if search is not None else draft.search_effort
    timeout = SEARCH_SECONDS[effort]
    
    start_time = time.perf_counter()
    
    model = cp_model.CpModel()
    
    employees = list(draft.employees)
    employee_ids = [e.id for e in employees]
    employee_by_id = {e.id: e for e in employees}
    
    services = list(draft.hours.services)
    
    work = {}
    start = {}
    end = {}
    post = {}
    
    for e in employees:
        for d in range(CYCLE_DAYS):
            weekday = WEEKDAYS[d % 7]
            for s_id in services:
                if draft.hours.is_closed(weekday, s_id):
                    continue
                structure = draft.structure_for(e.team, s_id, weekday)
                if structure is None:
                    continue
                    
                key = (e.id, d, s_id)
                work[key] = model.NewBoolVar(f"work_{e.id}_{d}_{s_id}")
                
                windows = derive_post_windows(structure)
                if not windows:
                    continue
                    
                min_start = min(w.start_minutes for w in windows)
                max_end = max(w.end_minutes for w in windows)
                min_level = min(w.level for w in windows)
                max_level = max(w.level for w in windows)
                
                start[key] = model.NewIntVar(min_start, max_end, f"start_{e.id}_{d}_{s_id}")
                end[key] = model.NewIntVar(min_start, max_end, f"end_{e.id}_{d}_{s_id}")
                post[key] = model.NewIntVar(min_level, max_level, f"post_{e.id}_{d}_{s_id}")
                
                model.Add(start[key] >= min_start).OnlyEnforceIf(work[key])
                model.Add(end[key] <= max_end).OnlyEnforceIf(work[key])
                model.Add(end[key] > start[key]).OnlyEnforceIf(work[key])
                
                model.Add(post[key] <= e.level).OnlyEnforceIf(work[key])
    
    for e in employees:
        for week_start in range(0, CYCLE_DAYS, 7):
            rest_days = []
            for d in range(week_start, min(week_start + 7, CYCLE_DAYS)):
                is_rest = model.NewBoolVar(f"rest_{e.id}_{d}")
                day_works = [
                    work.get((e.id, d, s_id))
                    for s_id in services
                    if (e.id, d, s_id) in work
                ]
                if day_works:
                    model.Add(sum(day_works) == 0).OnlyEnforceIf(is_rest)
                    model.Add(sum(day_works) >= 1).OnlyEnforceIf(is_rest.Not())
                else:
                    model.Add(is_rest == 1)
                rest_days.append(is_rest)
            model.Add(sum(rest_days) >= 2)
    
    for e in employees:
        for week_start in range(0, CYCLE_DAYS, 7):
            duration_terms = []
            for d in range(week_start, min(week_start + 7, CYCLE_DAYS)):
                for s_id in services:
                    key = (e.id, d, s_id)
                    if key in work and key in start and key in end:
                        dur = model.NewIntVar(0, 24 * 60, f"dur_{e.id}_{d}_{s_id}")
                        model.Add(dur == end[key] - start[key]).OnlyEnforceIf(work[key])
                        model.Add(dur == 0).OnlyEnforceIf(work[key].Not())
                        duration_terms.append(dur)
            if duration_terms:
                model.Add(sum(duration_terms) <= int(MAX_WEEKLY_HOURS * 60))
    
    min_rest_minutes = int(MIN_REST_BETWEEN_DAYS_HOURS * 60)
    for e in employees:
        for d in range(CYCLE_DAYS - 1):
            for s1 in services:
                key1 = (e.id, d, s1)
                if key1 not in work or key1 not in end:
                    continue
                for s2 in services:
                    key2 = (e.id, d + 1, s2)
                    if key2 not in work or key2 not in start:
                        continue
                    both_work = model.NewBoolVar(f"both_{e.id}_{d}_{s1}_{s2}")
                    model.AddBoolAnd([work[key1], work[key2]]).OnlyEnforceIf(both_work)
                    model.AddBoolOr([work[key1].Not(), work[key2].Not()]).OnlyEnforceIf(both_work.Not())
                    
                    rest_time = model.NewIntVar(0, 24 * 60 * 2, f"rest_{e.id}_{d}_{s1}_{s2}")
                    model.Add(rest_time == (24 * 60 - end[key1]) + start[key2]).OnlyEnforceIf(both_work)
                    model.Add(rest_time >= min_rest_minutes).OnlyEnforceIf(both_work)
    
    max_gap_minutes = int(MAX_COUPURE_HOURS * 60)
    for e in employees:
        for d in range(CYCLE_DAYS):
            day_services = [s_id for s_id in services if (e.id, d, s_id) in work]
            if len(day_services) < 2:
                continue
            for i, s1 in enumerate(day_services):
                for s2 in day_services[i+1:]:
                    key1 = (e.id, d, s1)
                    key2 = (e.id, d, s2)
                    both = model.NewBoolVar(f"coupure_{e.id}_{d}_{s1}_{s2}")
                    model.AddBoolAnd([work[key1], work[key2]]).OnlyEnforceIf(both)
                    model.AddBoolOr([work[key1].Not(), work[key2].Not()]).OnlyEnforceIf(both.Not())
                    
                    gap = model.NewIntVar(-24 * 60, 24 * 60, f"gap_{e.id}_{d}_{s1}_{s2}")
                    model.Add(gap == start[key2] - end[key1]).OnlyEnforceIf(both)
                    model.Add(gap <= max_gap_minutes).OnlyEnforceIf(both)
    
    for e in employees:
        for s_id, limit in e.wellbeing.max_services.items():
            if limit == 0:
                for d in range(CYCLE_DAYS):
                    key = (e.id, d, s_id)
                    if key in work:
                        model.Add(work[key] == 0)
    
    empty_posts = []
    for d in range(CYCLE_DAYS):
        weekday = WEEKDAYS[d % 7]
        for s_id in services:
            if draft.hours.is_closed(weekday, s_id):
                continue
            for team in Team:
                structure = draft.structure_for(team, s_id, weekday)
                if structure is None:
                    continue
                windows = derive_post_windows(structure)
                team_employees = [e for e in employees if e.team == team]
                
                for idx, window in enumerate(windows):
                    filled = model.NewBoolVar(f"filled_{d}_{s_id}_{team.value}_{idx}")
                    eligible_works = []
                    for e in team_employees:
                        key = (e.id, d, s_id)
                        if key in work and e.level >= window.level:
                            covers = model.NewBoolVar(f"covers_{e.id}_{d}_{s_id}_{idx}")
                            model.Add(start[key] <= window.start_minutes).OnlyEnforceIf(covers)
                            model.Add(end[key] >= window.end_minutes).OnlyEnforceIf(covers)
                            model.Add(post[key] == window.level).OnlyEnforceIf(covers)
                            model.AddImplication(covers, work[key])
                            eligible_works.append(covers)
                    
                    if eligible_works:
                        model.Add(sum(eligible_works) >= 1).OnlyEnforceIf(filled)
                        model.Add(sum(eligible_works) == 0).OnlyEnforceIf(filled.Not())
                    else:
                        model.Add(filled == 0)
                    
                    empty = model.NewBoolVar(f"empty_{d}_{s_id}_{team.value}_{idx}")
                    model.Add(empty == 1 - filled)
                    empty_posts.append(empty)
    
    hour_gaps = []
    for e in employees:
        total_hours = model.NewIntVar(0, int(MAX_WEEKLY_HOURS * 60 * 2), f"total_{e.id}")
        terms = []
        for d in range(CYCLE_DAYS):
            for s_id in services:
                key = (e.id, d, s_id)
                if key in work and key in start and key in end:
                    dur = model.NewIntVar(0, 24 * 60, f"dur2_{e.id}_{d}_{s_id}")
                    model.Add(dur == end[key] - start[key]).OnlyEnforceIf(work[key])
                    model.Add(dur == 0).OnlyEnforceIf(work[key].Not())
                    terms.append(dur)
        if terms:
            model.Add(total_hours == sum(terms))
        else:
            model.Add(total_hours == 0)
        
        contract_minutes = int(e.contractual_hours_per_week * 60 * 2)
        gap = model.NewIntVar(0, contract_minutes * 2, f"gap_{e.id}")
        diff = model.NewIntVar(-contract_minutes * 2, contract_minutes * 2, f"diff_{e.id}")
        model.Add(diff == total_hours - contract_minutes)
        model.AddAbsEquality(gap, diff)
        hour_gaps.append(gap)
    
    overqual_terms = []
    for e in employees:
        for d in range(CYCLE_DAYS):
            for s_id in services:
                key = (e.id, d, s_id)
                if key in work and key in post:
                    oq = model.NewIntVar(0, 10, f"oq_{e.id}_{d}_{s_id}")
                    model.Add(oq == e.level - post[key]).OnlyEnforceIf(work[key])
                    model.Add(oq == 0).OnlyEnforceIf(work[key].Not())
                    overqual_terms.append(oq)
    
    objective_terms = []
    if empty_posts:
        objective_terms.append(W_EMPTY * sum(empty_posts))
    if hour_gaps:
        objective_terms.append(sum(hour_gaps))
    if overqual_terms:
        objective_terms.append(W_OVERQ * sum(overqual_terms))
    
    if objective_terms:
        model.Minimize(sum(objective_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 1
    
    status = solver.Solve(model)
    
    solve_time_ms = int((time.perf_counter() - start_time) * 1000)
    
    status_name = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "invalid",
        cp_model.UNKNOWN: "unknown",
    }.get(status, "unknown")
    
    objective_value = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        objective_value = int(solver.ObjectiveValue())
    
    assignments: list[Shift] = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for e in employees:
            for d in range(CYCLE_DAYS):
                weekday = WEEKDAYS[d % 7]
                for s_id in services:
                    key = (e.id, d, s_id)
                    if key in work and solver.Value(work[key]):
                        structure = draft.structure_for(e.team, s_id, weekday)
                        if structure is None:
                            continue
                        windows = derive_post_windows(structure)
                        if not windows:
                            continue
                        
                        start_val = solver.Value(start[key])
                        end_val = solver.Value(end[key])
                        post_val = solver.Value(post[key])
                        
                        shift = Shift(
                            employee_id=e.id,
                            day_index=d,
                            weekday=weekday,
                            service_id=s_id,
                            team=e.team,
                            start_minutes=start_val,
                            end_minutes=end_val,
                            post_level=post_val,
                        )
                        assignments.append(shift)
    
    result = evaluate(draft.with_assignments(tuple(assignments)))
    key = _attempt_key(draft, result)
    empty, interdit, hours_miss, souhait, below_role, overqual = key
    
    trace = SearchTrace(
        seeder="cp-sat",
        seed_index=0,
        n_locks=0,
        calendars_by_seeder={"cp-sat": 1},
        calendars_total=1,
        seeds_infeasible=0,
        attempt_key={
            "empty": empty,
            "interdit": interdit,
            "hours_miss": hours_miss,
            "souhait": souhait,
            "below_role": below_role,
            "overqual": overqual,
            "solver_status": status_name,
            "objective_value": objective_value,
            "solve_time_ms": solve_time_ms,
        },
    )
    
    return EngineResult(
        assignments=tuple(assignments),
        warnings=result.warnings,
        trace=trace,
    )
