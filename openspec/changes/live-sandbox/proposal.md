## Why

After `generate_team`, the restaurateur edits that team’s published cycle without opening Saint-Cloud’s toy sandbox. Salle and cuisine need independent drafts so one team can be retuned, discarded, or published while the other stays untouched.

## What Changes

- `RestaurantState.live_sandboxes` holds an independent `Sandbox | None` for salle and cuisine. Empty restaurant and Saint-Cloud hydrate: both `None`. `state.sandbox` unchanged.
- `enter_live_sandbox(state, team)` copies the published cycle’s draft + result. Missing publish → `NoPublishedCycle`. Re-enter returns the same draft and history.
- `discard_live_sandbox(state, team)` drops that team’s draft only; the published cycle stays. Re-enter starts from the intact published cycle.
- `publish_live_sandbox(state, team)` writes `published_cycles[team]` from the current draft (assignments + warnings). No calendar weeks, no reconciliation. The other team’s cycle stays intact.
- Existing `preview_*` / `apply_proposal` / `undo_sandbox` route to `live_sandboxes[team]` when `team` is passed. Saint-Cloud keeps using `state.sandbox`.
- No HTTP, jobs, engine formula changes, or hydrate edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: a live restaurant may hold two independent team sandboxes on published cycles, separate from the single Saint-Cloud `state.sandbox`.

## Impact

- `src/doux_planning/context.py` (`NoPublishedCycle`, enter / discard / publish live). `RestaurantState` gains `live_sandboxes` with a harmless default.
- `PlanningStore` preview / apply / undo accept an optional `team` to select the live draft.
- Tests: salle generate + enter + cran + undo + discard; publish salle only; cuisine `NoPublishedCycle`. Existing Saint-Cloud pytest stays green.
- Do not edit `web/`, `api/`, `contracts/`, `engine.py` formulas, hydrate Saint-Cloud, or `state.sandbox` toy behavior.
