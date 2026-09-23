## Why

The restaurateur needs a checkbox for “at least one rest day each weekend” that is independent of the full-weekend radio. That wish was dropped with the old list key and must come back as a bool on the fiche.

## What Changes

- Add `Wellbeing.weekend_rest_day: bool` (default `false`), stackable with `weekend` radio.
- Warning + rest solver: each week, Saturday **or** Sunday off. A fully closed weekday counts as rest.
- `employee_board` grows `{ kind: "weekend_rest_day", held }` when the box is posed.
- Hydrate reads the object bool; missing key → `false`. List key `at_least_one_weekend_rest_day` stays refused (no alias).
- Do not rewrite Saint-Cloud `planning` (absent key = false; stats stay 92 / 17 / 10/12). No HTTP, no `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: `weekend_rest_day` wish, warning code, solver aim, board row, and hydrate default.

## Impact

- `staff.py`, `engine.py` (warning + rest model), `context.py` (board wishes), `hydrate.py`.
- Tests: freeze scenarios + domain / engine / board / hydrate. Do not edit `web/`, `api/`, `contracts/`, or `data/examples/saint-cloud.json` planning.
