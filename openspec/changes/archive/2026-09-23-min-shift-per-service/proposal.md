## Why

A fiche currently has one `min_shift_hours` scalar for every service. A restaurateur who can work a 3-hour evening closer still cannot keep a 4-hour midday minimum. The freeze (file 68) makes that minimum per offered service, default 4 h everywhere.

## What Changes

- **BREAKING (Core model):** `Employee.min_shift_hours` becomes a sparse mapping `morning|midday|evening` → float. Empty mapping means 4 h on every service. Lookup is `min_shift_for(employee, service_id)` (missing or unknown service → 4). A value ≤ 0 still raises `ValueError`.
- Generation stretch is unchanged (`stretch_to_min_shift` body stays as-is). Every `_assigned_window` reads the hours for `structure.service_id`.
- Sandbox Core (`preview_retune`, `preview_fill`, `_fill_hours`) uses `min_shift_for` for that slot’s `service_id`.
- Hydrate / bench JSON: a number `N` is still accepted. `N == 4` or omitted → `{}`; otherwise apply `N` on the services present in that draft. No `continuous` keys. Do not rewrite `data/examples/saint-cloud.json`.
- HTTP GET `employees[].min_shift_hours` is an **object** (one key per offered company service, value = `min_shift_for`, default 4). Never a number.
- PATCH / import: object (sparse OK) or number (compat: `4` → `{}`; other N → offered services, else the three company keys). Invalid key / ≤ 0 → 400 `Champs invalides.`
- Alembic: `staff_fiches.min_shift_hours` float → JSONB (`4` → `{}`; other N → the three keys at N).
- PATCH `services` that unchecks a service drops that key from every fiche map before persist. Export = GET employees without `invite_token`.
- UI steppers stay out of this Infra slice.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: each fiche stores a per-service minimum shift map (default 4 h), not one scalar for all services.
- `constraint-engine`: generation stretches or rejects a post using that employee’s minimum for the post’s `service_id`.
- `cruise-planning`: sandbox retune/fill duration checks use the same per-service minimum.
- `build-planning-api`: persist and HTTP GET/PATCH/import/export the per-service map (JSONB, never a number on GET).

## Impact

- `src/doux_planning/staff.py` (`Employee.min_shift_hours`, `min_shift_for`, coerce/validate).
- `src/doux_planning/engine.py` and vendored `engines/*.py` `_assigned_window` call sites only (hours argument).
- `src/doux_planning/planning.py` sandbox fill/retune.
- `src/doux_planning/hydrate.py` (and bench/context callers of `_employee`).
- Tests: domain, engine stretch, hydrate numeric 3, Saint-Cloud pytest; TestClient GET/PATCH/import/uncheck (skipif without `DATABASE_URL`).
- Infra may edit `src/doux_planning/api/` + Alembic after `20260921_0015`. Do not edit `web/`, `contracts/`, `engine.py` formulas, or the Saint-Cloud JSON file.
