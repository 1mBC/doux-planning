## Why

A live restaurant can be ready for salle without cuisine. Generation must publish one team’s cycle without touching the other, wrapping the existing solver. Saint-Cloud’s single `cycle` stays the example snapshot.

## What Changes

- `RestaurantState.published_cycles` holds independent `PublishedCycle | None` for salle and cuisine. Empty restaurant: both `None`. Saint-Cloud `cycle` unchanged.
- `generate_team(state, team, search)` : if `team_ready` is false, raise `TeamNotReady` and do not call `generate_cycle`. Otherwise expand the typical week, draft that team only, call `generate_cycle`, write `published_cycles[team]`. The other team’s cycle is left intact. Re-generate replaces only that team.
- `search` is `SearchEffort` (default optimized). Tests use `minimal` only.
- No HTTP, jobs, calendar weeks, sandbox live, or engine formula changes.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: two published team cycles on the live restaurant; `generate_team` wraps `generate_cycle` without a second solver.

## Impact

- `src/doux_planning/context.py` (`generate_team`, `TeamNotReady`). `RestaurantState` gains `published_cycles` with a harmless default.
- Tests for salle-only generate, cuisine `TeamNotReady` without solve, salle replace. Existing pytest stays green.
- Do not edit `web/`, `api/`, `contracts/`, `engine.py` formulas / `SEARCH_SECONDS`, preview/fill, or Saint-Cloud hydrate.
