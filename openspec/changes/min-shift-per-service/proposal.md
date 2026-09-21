## Why

A fiche currently has one `min_shift_hours` scalar for every service. A restaurateur who can work a 3-hour evening closer still cannot keep a 4-hour midday minimum. The freeze (file 68) makes that minimum per offered service, default 4 h everywhere.

## What Changes

- **BREAKING (Core model):** `Employee.min_shift_hours` becomes a sparse mapping `morning|midday|evening` → float. Empty mapping means 4 h on every service. Lookup is `min_shift_for(employee, service_id)` (missing or unknown service → 4). A value ≤ 0 still raises `ValueError`.
- Generation stretch is unchanged (`stretch_to_min_shift` body stays as-is). Every `_assigned_window` reads the hours for `structure.service_id`.
- Sandbox Core (`preview_retune`, `preview_fill`, `_fill_hours`) uses `min_shift_for` for that slot’s `service_id`.
- Hydrate / bench JSON: a number `N` is still accepted. `N == 4` or omitted → `{}`; otherwise apply `N` on the services present in that draft. No `continuous` keys. Do not rewrite `data/examples/saint-cloud.json`.
- HTTP and UI (object on GET, steppers per service, Alembic JSONB) are out of this Core change.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: each fiche stores a per-service minimum shift map (default 4 h), not one scalar for all services.
- `constraint-engine`: generation stretches or rejects a post using that employee’s minimum for the post’s `service_id`.
- `cruise-planning`: sandbox retune/fill duration checks use the same per-service minimum.

## Impact

- `src/doux_planning/staff.py` (`Employee.min_shift_hours`, `min_shift_for`, coerce/validate).
- `src/doux_planning/engine.py` and vendored `engines/*.py` `_assigned_window` call sites only (hours argument).
- `src/doux_planning/planning.py` sandbox fill/retune.
- `src/doux_planning/hydrate.py` (and bench/context callers of `_employee`).
- Tests: domain, engine stretch, hydrate numeric 3, Saint-Cloud pytest.
- Do not edit `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `stretch_to_min_shift` body, or the Saint-Cloud JSON file.
