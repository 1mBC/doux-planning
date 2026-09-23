## Why

Live enter currently requires a published cycle, which only `generate_team` can create. The restaurateur needs a fourth, independent path: seed that team’s Core slot as an empty grid (types + fiches, zero assignments, scored by `evaluate`) so they can compose a cycle by hand with the existing live gestures.

## What Changes

- Add `seed_empty_team_cycle(state, team) -> PublishedCycle` next to `generate_team`. `team_ready` false → `TeamNotReady` and no engine. Ready team: same skeleton as `generate_team` (`expand_typical_week` filtered to the team, that team’s employees, `state.hours`, `default_legal_rules()`), `assignments = ()`, `result = evaluate(draft)`, write `published_cycles[team]`. The other team stays intact.
- `draft.search_effort` stays the existing PlanningDraft default. Do not add `SearchEffort.MANUEL`. Do not call `generate_cycle` / `generate_for`.
- `enter_live_sandbox` / `publish_live_sandbox` / `discard_live_sandbox` stay as they are (enter after seed). Reuse existing `preview_*` / `apply_proposal` / `undo_sandbox`. No new gesture.
- Saint-Cloud `state.sandbox` and hydrate stay unchanged.
- HTTP persist multiplexes four JSONB slots (`minimal|optimized|maximal|manuel`). Generate rejects `search_effort: "manuel"` (400). Enter `manuel` seeds or hydrates; publish writes `versions.manuel` without `generate_logs`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: a ready team can publish an empty scored cycle without running the solver, then enter the existing live sandbox on that seed.
- `build-planning-api`: persist four published slots including `manuel`; enter/publish/discard the manuel live draft; generate never writes that slot.

## Impact

- `src/doux_planning/context.py` (`seed_empty_team_cycle` next to `generate_team`).
- `src/doux_planning/api/generate.py` + `live_sandbox.py` (4-key coerce, enter seed, manuel publish).
- Tests: salle ready without `generate_team` → empty assignments + coverage `empty_post` + cuisine `None`; enter + fill/apply/undo; `TeamNotReady` if not ready; `generate_team(..., minimal)` afterwards replaces the Core salle slot; Saint-Cloud pytest stays green.
- HTTP tests (`skipif` without `DATABASE_URL`): enter manuel without generate; fill/commit; publish without `generate_logs`; generate keeps manuel; POST generate manuel 400; 3-key coerce.
- Do not edit `web/`, `contracts/`, Alembic, `SearchEffort`, engine formulas, `stretch_to_min_shift`, keep-best, Saint-Cloud hydrate, or bench `EFFORTS`.
