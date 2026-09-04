## Why

A linked employee must see their team’s **published** cycle (full grid) plus their own contract, unavailabilities, and wishes — never the live sandbox draft, and without a second solve.

## What Changes

- `employee_board(state, employee_id)` returns `EmployeeBoard`: team, all published-cycle assignments for that team, contract `{weekly, assigned, ok}`, wish rows from the fiche, and read-only unavailability patterns.
- Unknown fiche → existing `UnknownEmployee`. No published cycle → empty assignments, `assigned` 0.
- Wishes: one row per fiche `wellbeing` key; `held` is false when the published result has a matching `souhait` warning for that person (freeze mapping). Absent pref → no row.
- Never read `live_sandboxes`. Never call `generate_cycle`. `employee_view` (Saint-Cloud own-shifts) stays unchanged.
- No HTTP, jobs, preview/fill, hydrate, or engine formula changes.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: a live employee board reads the published team cycle (full grid + contract/wishes), not the live draft and not `employee_view`.

## Impact

- `src/doux_planning/context.py` (`employee_board`, `EmployeeBoard`). Reuse `UnknownEmployee` from invites.
- Tests: salle generate + wish, unpublished live cran invisible, cuisine without cycle empty, unknown id. Existing pytest including `employee_view` stays green.
- Do not edit `web/`, `api/`, `contracts/`, `engine.py` formulas, preview/fill, hydrate, or `employee_view`.
