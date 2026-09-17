from __future__ import annotations

from doux_planning.engine import EngineResult, PlanningDraft, SearchTrace, _attempt_key, generate_cycle
from doux_planning.engines import core_0, core_1, core_2, core_3, core_4, core_6, cp_0, iter_0
from doux_planning.types import SearchEffort

ENGINE_REFS = ("core-0", "core-1", "core-2", "core-3", "core-4", "core-5", "core-6", "cp-0", "iter-0")
_FROZEN = {
    "core-0": core_0,
    "core-1": core_1,
    "core-2": core_2,
    "core-3": core_3,
    "core-4": core_4,
    "core-6": core_6,
    "cp-0": cp_0,
    "iter-0": iter_0,
}
_SEEDS_ENGINES = frozenset({"core-3", "core-4", "core-6"})
_CUSTOM_TRACE_ENGINES = frozenset({"cp-0", "iter-0"})


class UnknownEngineRef(KeyError):
    def __init__(self, engine_ref: str) -> None:
        self.engine_ref = engine_ref
        super().__init__(engine_ref)


def list_engine_refs() -> tuple[str, ...]:
    return ENGINE_REFS


def generate_for(
    engine_ref: str, draft: PlanningDraft, search: SearchEffort | None = None
) -> tuple[EngineResult, SearchTrace]:
    if engine_ref not in ENGINE_REFS:
        raise UnknownEngineRef(engine_ref)
    if engine_ref == "core-5":
        result = generate_cycle(draft, search)
        assert result.trace is not None
        return result, result.trace
    module = _FROZEN[engine_ref]
    result = module.generate_cycle(draft, search)
    if engine_ref in _SEEDS_ENGINES or engine_ref in _CUSTOM_TRACE_ENGINES:
        assert result.trace is not None
        trace = SearchTrace(
            seeder=result.trace.seeder,
            seed_index=result.trace.seed_index,
            n_locks=result.trace.n_locks,
            calendars_by_seeder=result.trace.calendars_by_seeder,
            calendars_total=result.trace.calendars_total,
            seeds_infeasible=result.trace.seeds_infeasible,
            attempt_key=result.trace.attempt_key,
        )
        return result, trace
    filled = int(module.SEARCH_PROGRESS.get("calendars", 0))
    key = _attempt_key(draft, result)
    empty, interdit, hours_miss, souhait, below_role, overqual = key
    trace = SearchTrace(
        seeder="empty",
        seed_index=0,
        n_locks=0,
        calendars_by_seeder={"empty": filled},
        calendars_total=filled,
        seeds_infeasible=0,
        attempt_key={
            "empty": empty,
            "interdit": interdit,
            "hours_miss": hours_miss,
            "souhait": souhait,
            "below_role": below_role,
            "overqual": overqual,
        },
    )
    return result, trace
