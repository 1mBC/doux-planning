## Context

See proposal.md. Legal rest 11h, two weekly rests, 5h coupure, 4h min shift, and contract tolerance stay as they are. `employee_view` and Saint-Cloud `state.sandbox` stay. Do not edit `api/` or `contracts/`.

## Goals / Non-Goals

**Goals:**
- Structured `Wellbeing` + exact `Unavailability` + `week_label_scheme`.
- Warnings and rest/fill solver aim at the same wishes.
- Hydrate new JSON only. Board wish rows `{ kind, held, … }`.

**Non-Goals:**
- HTTP persist, UI tabs, seed button, example HTTP contract edits.

## Decisions

### 1. `Wellbeing` on the fiche, not an enum set

`WeekendChoice` is `every_two` | `even` | `odd`. `max_services` is a mapping of present keys only. Default `Wellbeing()` is all-off. `Employee.max_evenings_per_week` / `max_mornings_per_week` are removed.

### 2. Consecutive rest uses circular weekdays and closed days

Pairs include Fri–Sat, Sat–Sun, Sun–Mon. A fully closed weekday counts as rest. Solver pair constraints use the same pairs.

### 3. Hydrate refuses legacy keys

A list `wellbeing`, deleted enum strings, `every_*` on indispos, or leftover `max_*_per_week` fields raise. Saint-Cloud employees are rewritten to the new object form.

### 4. Board mapping lives in this change

`BoardWish` uses `kind` plus optional `value` / `service_id` / `limit`. Held still means no matching published `souhait` code. Do not `/opsx-update` employee-board.

### 5. Recompute snapshot only if generate changes

Compare `generate_cycle(..., optimized)` assignments to the file. Identical → leave `planning`. Different → rewrite `planning` and report new stats; do not edit `contracts/http/v1-examples.md`.

## Risks / Trade-offs

- [HTTP api still sends `wellbeing: []`] → Do not patch `api/`; list failing tests.
- [Sat–Sun now counts as consecutive rest] → Existing engine tests that assumed the opposite are updated to the freeze.

## Migration Plan

Snapshot employees this change. Persist/HTTP is the next Infra brief.

## Open Questions

None.
