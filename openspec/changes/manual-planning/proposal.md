## Why

Live enter currently requires a published cycle, which only `generate_team` can create. The restaurateur needs a fourth, independent path: seed that team’s Core slot as an empty grid (types + fiches, zero assignments, scored by `evaluate`) so they can compose a cycle by hand with the existing live gestures.

## What Changes

- Add `seed_empty_team_cycle(state, team) -> PublishedCycle` next to `generate_team`. `team_ready` false → `TeamNotReady` and no engine. Ready team: same skeleton as `generate_team` (`expand_typical_week` filtered to the team, that team’s employees, `state.hours`, `default_legal_rules()`), `assignments = ()`, `result = evaluate(draft)`, write `published_cycles[team]`. The other team stays intact.
- `draft.search_effort` stays the existing PlanningDraft default. Do not add `SearchEffort.MANUEL`. Do not call `generate_cycle` / `generate_for`.
- `enter_live_sandbox` / `publish_live_sandbox` / `discard_live_sandbox` stay as they are (enter after seed). Reuse existing `preview_*` / `apply_proposal` / `undo_sandbox`. No new gesture.
- Saint-Cloud `state.sandbox` and hydrate stay unchanged.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: a ready team can publish an empty scored cycle without running the solver, then enter the existing live sandbox on that seed.

## Impact

- `src/doux_planning/context.py` (`seed_empty_team_cycle` next to `generate_team`).
- Tests: salle ready without `generate_team` → empty assignments + coverage `empty_post` + cuisine `None`; enter + fill/apply/undo; `TeamNotReady` if not ready; `generate_team(..., minimal)` afterwards replaces the Core salle slot; Saint-Cloud pytest stays green.
- Do not edit `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `SearchEffort`, engine formulas, `stretch_to_min_shift`, keep-best, or Saint-Cloud hydrate.
