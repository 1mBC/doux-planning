# Design

## Context

See proposal.md. `generate_team` is the only Core writer of `published_cycles[team]` today: it builds a team-filtered `PlanningDraft` and calls `generate_cycle` / `generate_for`. `enter_live_sandbox` already requires that published slot. Freeze file 69 Core wins: seed an empty scored cycle, then enter. Do not change FIFO, keep-best, formulas, `stretch_to_min_shift`, `SearchEffort`, hydrate, or `state.sandbox`.

## Goals / Non-Goals

**Goals:**
- Seed a ready team's published cycle as empty assignments + `evaluate` warnings.
- Leave Core live enter / discard / publish and existing gestures untouched.
- HTTP persist four JSONB slots including `manuel`; enter can seed a live draft without writing the published slot until publish.

**Non-Goals:**
- Alembic, UI cran, `SearchEffort.MANUEL`, solver on the manual path, new gestures, bench `manuel` effort.

## Decisions

### 1. Function next to `generate_team`

`seed_empty_team_cycle(state, team) -> PublishedCycle` lives in `context.py`. Same readiness gate (`TeamNotReady`) and same draft skeleton as `generate_team` (team-filtered `expand_typical_week`, team employees, `state.hours`, `default_legal_rules()`). `assignments = ()`. Omit `search_effort=` so the draft keeps `PlanningDraft`'s existing default (`OPTIMIZED`). `result = evaluate(draft)` from `engine.py` (already imported). Write `published_cycles[team]` and return that `PublishedCycle`.

Alternative: reuse `generate_cycle` with a dummy effort — rejected; freeze forbids solver on this path.

### 2. Live API unchanged

`enter_live_sandbox` still requires a published cycle; callers seed first. `publish_live_sandbox` / `discard_live_sandbox` stay as they are. Preview / apply / undo already accept `team`.

### 3. Tests reuse `_complete_salle`

Salle-ready fixture from `test_team_generate` without `generate_team`. Fill uses `FillSlot` for Emma monday midday (the fixture's only structure). Patch `generate_cycle` / `generate_for` on the seed path to prove they are not called.

### 4. HTTP slot multiplex (`build-planning-api`)

`SLOT_KEYS = minimal|optimized|maximal|manuel`. Compute `EFFORTS` and bench `EFFORTS` stay the three solves. `normalize_team_published` always emits four keys; 3-key blobs and flat cycles gain `manuel: null`. `POST /v1/generate` with `manuel` is 400 and never writes that slot. Live enter with `search_effort=manuel` and a null slot calls Core `seed_empty_team_cycle` then persist live only. Publish of that draft uses a new `generated_at` (not keep-`generated_at`), omits duration/engine_ref, and does not insert `generate_logs`. Discard of a never-published manuel draft re-seeds empty.

## Risks / Trade-offs

- [Empty grid has no assignment to retune] → tests fill instead of retune, matching freeze "fill/apply/undo".
- [Default search_effort looks like a compute slot] → Core `published_cycles` is still one cycle per team; multiplex is Infra. Do not add `MANUEL`.

## Migration Plan

None for snapshot data.

## Open Questions

None.
