# Design

## Context

See proposal.md. `Employee.min_shift_hours` is a float defaulting to `DEFAULT_MIN_SHIFT_HOURS` (4). `stretch_to_min_shift(window, min_hours, structure)` already takes a float; `_assigned_window` in live `engine.py` and every vendored `engines/core_*.py` passes `employee.min_shift_hours`. Sandbox `preview_retune` / `preview_fill` / `_fill_hours` multiply the same scalar. Hydrate and bench JSON store a number (Saint-Cloud uses `4.0`). Freeze file 68 Core wins; `stretch_to_min_shift` body must stay byte-identical.

## Goals / Non-Goals

**Goals:**
- Sparse per-service map on the fiche; lookup default 4.
- Same stretch formula, different hours argument per `service_id`.
- Numeric JSON compat for hydrate/bench without rewriting Saint-Cloud.
- HTTP GET object (one key per offered service), PATCH/import object or number, Alembic JSONB, smash dropped service keys on every fiche.

**Non-Goals:**
- UI steppers (`web/`).
- Restaurant-wide minimum, quarter-hour snapping, `continuous` keys.
- Changing pairing/FIFO or stretch end-then-start.
- Rewriting Core `coerce_min_shift_hours` / `min_shift_for` / `engine.py` formulas.

## Decisions

### 1. Lookup helper next to `Employee`

`min_shift_for(employee, service_id) -> float` returns the map value or `DEFAULT_MIN_SHIFT_HOURS`. Unknown service (including `continuous`) is 4. Validation of values ≤ 0 stays in `Employee.__post_init__` with the same `ValueError` message as today. Keys outside `morning|midday|evening` are rejected like `max_services`. Freeze the map with `MappingProxyType`, same as `Wellbeing.max_services`.

Alternative: methods on `Employee` — rejected; freeze names the free function.

### 2. Engine copies get the hours argument only

Every `_assigned_window` computes `hours = min_shift_for(employee, structure.service_id)` and passes that to `stretch_to_min_shift` and the duration check. Do not inline a different stretch. Vendored engines stay in lockstep so bench refs do not silently keep the scalar.

### 3. Hydrate numeric N uses draft services, constructor float uses company services

JSON number 4 or omitted → `{}`. Other N → `{service_id: N}` for company services present on that draft (`hours.services` / structure ids, never `continuous`). A JSON object is stored sparse. If Core constructs `Employee(min_shift_hours=3.0)` (legacy float, including unpatched API rows), coerce N≠4 onto `COMPANY_SERVICE_IDS` so existing constructors do not crash.

Alternative: reject floats on `Employee` — rejected; hydrate/bench and current tests/API still pass numbers.

### 4. Sandbox reads the slot’s `service_id`

`preview_retune` uses `shift.service_id`. `_fill_hours` and `preview_fill` use `slot.service_id` (including when scoring replacement candidates).

### 5. HTTP wraps Core coerce / lookup (Infra)

GET fills `{ service_id: min_shift_for(person, service_id) }` for `state.company_services` — never a scalar. PATCH / import calls `coerce_min_shift_hours` (do not reimplement): a number `4` → `{}`; other N uses offered services when present, else `morning|midday|evening`. Invalid key / ≤ 0 maps to HTTP 400 `Champs invalides.` `_fiche_to_employee` / persist store the mapping (JSONB), not `float(min_shift)`.

Unchecking a service (PATCH `services`) drops that key from every fiche `min_shift_hours` map before persist, same smash as unavail / `max_services`. GET must not emit the dropped service. Export reuses serialize_context employees without `invite_token`.

### 6. Alembic after `20260921_0015`

`staff_fiches.min_shift_hours` Float → JSONB. `4` → `{}`; other N → `{"morning":N,"midday":N,"evening":N}`. Default `'{}'::jsonb`.

## Risks / Trade-offs

- [Vendored engines drift] → same `_assigned_window` edit in every `core_*.py` that calls stretch.
- [Empty map vs explicit 4s] → empty is the canonical default so Saint-Cloud hydrate of `4.0` does not materialize three keys. GET still emits 4 for each offered service.
- [JSONB vs MappingProxyType] → persist `dict(...)` and `flag_modified`; serialize a plain dict.

## Migration Plan

Alembic after `20260921_0015` converts the float column. Example JSON stays numeric 4; hydrate maps it to `{}`.

## Open Questions

None.
