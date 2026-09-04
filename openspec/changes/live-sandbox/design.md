## Context

See proposal.md. `generate_team` already writes `published_cycles`. Preview / apply / undo already exist on `PlanningStore` for Saint-Cloud `state.sandbox`. Do not change FIFO, keep-best, formulas, or hydrate.

## Goals / Non-Goals

**Goals:**
- Enter / discard / publish a live draft per team on the published cycle.
- Route existing preview / apply / undo to that draft when `team` is passed.

**Non-Goals:**
- HTTP, jobs, calendar weeks, reconciliation, a second gesture set, changing `state.sandbox`.

## Decisions

### 1. Live API lives in `context.py`

Same module as `generate_team`. `NoPublishedCycle`, `enter_live_sandbox`, `discard_live_sandbox`, `publish_live_sandbox` mutate `RestaurantState`. Enter copies draft + result from `published_cycles[team]`. Re-enter returns the existing `live_sandboxes[team]`. Discard sets that slot to `None`. Publish writes `PublishedCycle` from the current draft/result and clears that live slot so the next enter is a fresh copy of the new published cycle.

### 2. `live_sandboxes` default on `RestaurantState`

`{Team.SALLE: None, Team.CUISINE: None}`. Empty restaurant and hydrate inherit it. Do not write `state.sandbox`.

### 3. Optional `team` routes the store

`_require_sandbox`, `apply_edit`, `preview_*`, `apply_proposal`, and `undo_sandbox` take `team: Team | None = None`. `None` keeps Saint-Cloud on `state.sandbox`. A team selects `live_sandboxes[team]`. Gesture ranking and evaluate calls stay as they are.

## Risks / Trade-offs

- [Generated salle shifts vary] → Tests pick the first assignment and retune by +15 minutes; use `SearchEffort.MINIMAL` only in setup.
- [Shared draft object with published] → Enter uses `replace(published.draft)` so assignment writes do not mutate the published draft until publish.

## Migration Plan

None for snapshot data.

## Open Questions

None.
