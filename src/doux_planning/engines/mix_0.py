# mix-0: mixture of experts (sequential, global picker)
from __future__ import annotations

import time

from doux_planning.engine import EngineResult, PlanningDraft, SearchTrace, _attempt_key
from doux_planning.types import SearchEffort

MIX0_EXPERTS = ("core-2", "core-2.1", "cp-0", "iter-0")

SEARCH_PROGRESS: dict[str, int] = {"calendars": 0}

MAXIMAL_TOTAL_SECONDS = 600.0
MAXIMAL_PER_EXPERT = MAXIMAL_TOTAL_SECONDS / len(MIX0_EXPERTS)


def generate_cycle(draft: PlanningDraft, search: SearchEffort | None = None) -> EngineResult:
    from doux_planning.context import cycle_score
    from doux_planning.engines.registry import generate_for
    
    effort = search if search is not None else draft.search_effort
    
    runs: list[dict] = []
    best_result: EngineResult | None = None
    best_trace: SearchTrace | None = None
    best_global: float | None = None
    best_key: tuple | None = None
    best_expert: str | None = None
    
    for expert in MIX0_EXPERTS:
        start = time.perf_counter()
        
        if effort == SearchEffort.MAXIMAL:
            from doux_planning.engines import core_2, core_2_1, cp_0, iter_0
            modules = {
                "core-2": core_2,
                "core-2.1": core_2_1,
                "cp-0": cp_0,
                "iter-0": iter_0,
            }
            if expert in modules:
                module = modules[expert]
                original_seconds = dict(module.SEARCH_SECONDS)
                module.SEARCH_SECONDS[SearchEffort.MAXIMAL] = MAXIMAL_PER_EXPERT
                try:
                    result, trace = generate_for(expert, draft, effort)
                finally:
                    module.SEARCH_SECONDS.update(original_seconds)
            else:
                result, trace = generate_for(expert, draft, effort)
        else:
            result, trace = generate_for(expert, draft, effort)
        
        elapsed = time.perf_counter() - start
        
        score = cycle_score(draft, result)
        global_score = score.global_score
        key = _attempt_key(draft, result)
        
        runs.append({
            "engine_ref": expert,
            "global": global_score,
            "attempt_key": {
                "empty": key[0],
                "interdit": key[1],
                "hours_miss": key[2],
                "souhait": key[3],
                "below_role": key[4],
                "overqual": key[5],
            },
            "duration_seconds": round(elapsed, 2),
        })
        
        is_better = False
        if best_global is None:
            is_better = True
        elif global_score is not None and best_global is not None:
            if global_score > best_global:
                is_better = True
            elif global_score == best_global:
                if key < best_key:
                    is_better = True
        
        if is_better:
            best_result = result
            best_trace = trace
            best_global = global_score
            best_key = key
            best_expert = expert
    
    assert best_result is not None
    assert best_key is not None
    
    empty, interdit, hours_miss, souhait, below_role, overqual = best_key
    
    trace = SearchTrace(
        seeder="mix",
        seed_index=0,
        n_locks=0,
        calendars_by_seeder={"mix": 1},
        calendars_total=1,
        seeds_infeasible=0,
        attempt_key={
            "empty": empty,
            "interdit": interdit,
            "hours_miss": hours_miss,
            "souhait": souhait,
            "below_role": below_role,
            "overqual": overqual,
        },
        repairs=None,
        mix={
            "experts": list(MIX0_EXPERTS),
            "picker": "global",
            "winner": best_expert,
            "runs": runs,
        },
    )
    
    SEARCH_PROGRESS["calendars"] = 1
    
    return EngineResult(
        assignments=best_result.assignments,
        warnings=best_result.warnings,
        trace=trace,
    )
