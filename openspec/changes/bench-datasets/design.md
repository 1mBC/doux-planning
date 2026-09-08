## Context

See proposal.md. Freeze: `contracts/domain/bench.md` (follow, do not edit). Four salle datasets already live under `data/bench/`. Live context helpers (`set_services`, `set_role_ladder`, `upsert_service_type`, `set_typical_week`, `upsert_employee`, `expand_typical_week`, `team_ready`, `cycle_score`) already exist. `generate_cycle` keep-best stays untouched.

## Goals / Non-Goals

**Goals:**
- Scan disk, load a disposable live context, run generate vs oracle scores.
- Isolation: never write `published_cycles`; never call `generate_team` on a persisted restaurant.

**Non-Goals:**
- HTTP / `bench_jobs` / `VERSION` persistence (Infra).
- UI. Cuisine datasets. Rewriting `data/bench/**` or Saint-Cloud.

## Decisions

### 1. Dedicated `bench.py`

Keeps scan / derive-week / `run_bench` off `context.py`. Reuses hydrate `_employee` / `_shift` so wellbeing and indispos match live fiches. Invite tokens come from `Employee` construction (generated, ≠ id).

### 2. Typical week is derived, not stored

`context.json` has no `typical_week`. Cells = each `roles.team` × `hours.services` × 7 weekdays. Closed iff weekday ∈ `closed_weekdays`. Otherwise the unique type `(team, service_id)`. Cuisine stays absent (no ladder, no fiches, no cells).

### 3. Hours closed days after `set_services`

`set_services` does not take `closed_weekdays`. Load calls it, then sets `RestaurantHours.multi_service(*services, closed_weekdays=...)` so evaluate / generate see Sunday closed.

### 4. `run_bench` never publishes

`load_bench_dataset` always builds a new `empty_restaurant` (disposable copy). `run_bench` loads again, builds a salle `PlanningDraft`, `generate_cycle(draft, effort)`, `cycle_score` on that result and on `evaluate(draft.with_assignments(expected))`. Do not call `generate_team`. Do not deepcopy the state (`Wellbeing.max_services` is a `mappingproxy`). Tests use `SearchEffort.MINIMAL` only.

### 5. `data/bench/VERSION` unread for persistence

Core may ignore the file. Infra persists `app_version` later.

## Risks / Trade-offs

- [Minimal generate on tight coverage] → Outcome still has scores and deltas; oracle is human, not maximal. Tests do not assert generated notes equal oracle.
- [Invite tokens differ each load] → Isolation tests compare the caller’s live state, not token equality across loads.

## Migration Plan

None. Infra wires HTTP later.

## Open Questions

None.
