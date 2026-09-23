## Context

See proposal.md. `generate_cycle(draft, search)` is the only solver. `team_ready` / `expand_typical_week` already exist. Do not change FIFO, keep-best, stretch, or `SEARCH_SECONDS`.

## Goals / Non-Goals

**Goals:**
- Wrap `generate_cycle` for one ready team.
- Keep the other published cycle intact.

**Non-Goals:**
- HTTP, jobs, calendar weeks, sandbox live, a second algorithm, changing Saint-Cloud `cycle`.

## Decisions

### 1. `generate_team` lives in `context.py`

Same module as `team_ready` / expand. Raises `TeamNotReady` before any `generate_cycle` import-call. Draft: employees and expanded structures filtered by `team`, `hours` from `set_services`, `legal_rules=default_legal_rules()` (france id on identity, no rule copy).

### 2. `published_cycles` default on `RestaurantState`

`{Team.SALLE: None, Team.CUISINE: None}`. Empty restaurant inherits it. Hydrate does not write it, so Saint-Cloud `cycle` stays the snapshot.

### 3. Tests use `SearchEffort.MINIMAL` only

Default parameter remains `optimized` for live callers. Tests never pass optimized/maximal.

## Risks / Trade-offs

- [Minimal generate still walks rest calendars] → One salle fiche / one midday type; keep tests on `minimal` only.
- [`as_draft` still uses `state.cycle` for Saint-Cloud] → Do not route example hydrate through `published_cycles`.

## Migration Plan

None for snapshot data.

## Open Questions

None.
