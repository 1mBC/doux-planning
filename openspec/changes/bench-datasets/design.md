## Context

See proposal.md. Freeze: `contracts/domain/bench.md` (follow, do not edit). Fifty salle datasets live under `data/bench/` (30 existing bit-identical + 20 new crafted oracles). Live context helpers already exist. `generate_cycle` keep-best stays untouched. `VERSION` stays `core-2`.

## Goals / Non-Goals

**Goals:**
- Scan disk (50 pairs), load a disposable live context (`typical_week` when present), run generate vs oracle scores.
- Add 20 planning-first crafted oracles (grid first, then deduced fiches) with 0 interdit / hours_miss / below_role and global ≥ 9.5.
- Isolation: never write `published_cycles`; never call `generate_team` on a persisted restaurant.

**Non-Goals:**
- HTTP / `bench_jobs` / `VERSION` persistence (Infra).
- HTTP / UI. Cuisine datasets. Rewriting the 30 existing dataset folders, `engine.py`, or Saint-Cloud. Changing `VERSION`. Changing `BENCH_CATEGORY_ORDER`.

## Decisions

### 1. Dedicated `bench.py`

Keeps scan / derive-week / `run_bench` off `context.py`. Reuses hydrate `_employee` / `_shift` so wellbeing and indispos match live fiches. Invite tokens come from `Employee` construction (generated, ≠ id).

### 2. Typical week from JSON when present, else derived

If `context.json` has `typical_week`, those cells win (one per `team × service × weekday`; `type_id` null iff closed). Several types may share a `service_id`. If the key is absent, keep the current derivation: one type per `(team, service)` — the 7 existing files stay on that path. Cuisine stays absent.

### 3. Hours closed days after `set_services`

`set_services` does not take `closed_weekdays`. Load calls it, then sets `RestaurantHours.multi_service(*services, closed_weekdays=...)` so evaluate / generate see Sunday closed.

### 4. `run_bench` never publishes

`load_bench_dataset` always builds a new `empty_restaurant` (disposable copy). `run_bench` loads again, builds a salle `PlanningDraft`, `generate_cycle(draft, effort)`, `cycle_score` on that result and on `evaluate(draft.with_assignments(expected))`. Do not call `generate_team`. Do not deepcopy the state (`Wellbeing.max_services` is a `mappingproxy`). Tests use `SearchEffort.MINIMAL` only.

### 5. `data/bench/VERSION` unread for persistence

Core may ignore the file. Infra persists `app_version` later.

### 6. Catalogue order includes the new families

`BENCH_CATEGORY_ORDER = ("tight", "clock", "wishes", "ladder", "crafted", "hours", "size", "overqual", "closed", "shapes")`. Scan still omits incomplete folders. Load / `run_bench` stay the same functions. The 30 existing folders are not rewritten.

### 8. New crafted oracles are planning-first

Write the 14-day `expected.json` that covers every open service, then deduce context so that grid is legal. `evaluate` must yield 0 `interdit`, `_hours_miss` 0, `_below_role_count` 0 (level == post). `cycle_score` global ≥ 9.5 (aim 10). The freeze table particularity is a constraint inside the oracle, not decoration.

### 7. Wider salle shapes, same engine

`hours.services` may include `morning`. Role `level` may be 1…6. Oracle rules unchanged: every expected has 0 `interdit`; each `crafted` expected `cycle_score` global ≥ 9.5. No fill / SAT / `SEARCH_*` change.

## Risks / Trade-offs

- [Minimal generate on tight coverage] → Outcome still has scores and deltas; oracle is human, not maximal. Tests do not assert generated notes equal oracle.
- [Invite tokens differ each load] → Isolation tests compare the caller’s live state, not token equality across loads.

## Migration Plan

None. Infra wires HTTP later.

## Open Questions

None.
