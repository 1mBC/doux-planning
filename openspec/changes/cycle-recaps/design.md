## Context

See proposal.md. `published_cycles[team].result` already has assignments and warnings. `employee_board` / `_board_wishes` is the posed-wish rule. `_below_role_count` is the below-role counter. Saint-Cloud `wish_cols` stay on the frozen file only.

## Goals / Non-Goals

**Goals:**
- Read-only `CycleRecap` on a published team cycle.
- French 11 h warning with both clocks.

**Non-Goals:**
- Second solve, HTTP persist, snapshot rewrite, translating other warning codes.

## Decisions

### 1. Recap lives in `context.py`

Same module as `employee_board` and `NoPublishedCycle`. It filters fiches and assignments to the team, counts stats from the stored result, and builds legal/wish tables. It imports `_below_role_count` so below-role is not a second formula.

### 2. Legal rule codes vs engine `max_daily_hours`

Engine still emits `max_daily_hours`. Recap maps that to `max_daily_salle` or `max_daily_cuisine` per team. Other legal cells key on the engine code. OK text follows the freeze (`OK · min 11h`, `N / 2 j.`, `max {durée}`, `{sem1}h / {sem2}h`). Not-OK `rest_between_days` reuses the enriched clock span.

### 3. Wish keys from posed board wishes

Column set = union of posed kinds on the team (plus always-on `contrat`, and `indispo` if any fiche has an unavailability). Cell is null when that fiche did not pose the wish. Contract / indispo / held texts follow the freeze. Weekend cell adds the French radio value.

### 4. Clocks in `evaluate` only for 11 h

`format_clock` matches the UI helper (`23h`, `11h30`). Weekday labels are `lundi`…`dimanche`. `day_index` stays the last-shift day (A).

## Risks / Trade-offs

- [Snapshot wish keys differ from live] → Accepted: file stays frozen; live recap uses the new model.

## Migration Plan

None for the snapshot. HTTP persist is Infra.

## Open Questions

None.
