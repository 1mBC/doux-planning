# Design

## Context

See proposal.md. `Employee.min_shift_hours` is a float defaulting to `DEFAULT_MIN_SHIFT_HOURS` (4). `stretch_to_min_shift(window, min_hours, structure)` already takes a float; `_assigned_window` in live `engine.py` and every vendored `engines/core_*.py` passes `employee.min_shift_hours`. Sandbox `preview_retune` / `preview_fill` / `_fill_hours` multiply the same scalar. Hydrate and bench JSON store a number (Saint-Cloud uses `4.0`). Freeze file 68 Core wins; `stretch_to_min_shift` body must stay byte-identical.

## Goals / Non-Goals

**Goals:**
- Sparse per-service map on the fiche; lookup default 4.
- Same stretch formula, different hours argument per `service_id`.
- Numeric JSON compat for hydrate/bench without rewriting Saint-Cloud.

**Non-Goals:**
- HTTP GET/PATCH shape, Alembic JSONB, UI steppers.
- Restaurant-wide minimum, quarter-hour snapping, `continuous` keys.
- Changing pairing/FIFO or stretch end-then-start.

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

## Risks / Trade-offs

- [API still serializes/persists a float column] → Core does not patch `api/`. HTTP tests that need `DATABASE_URL` may fail until Infra. In-memory Core tests must stay green.
- [Vendored engines drift] → same `_assigned_window` edit in every `core_*.py` that calls stretch.
- [Empty map vs explicit 4s] → empty is the canonical default so Saint-Cloud hydrate of `4.0` does not materialize three keys.

## Migration Plan

No schema migration in this change. Example JSON stays numeric 4; hydrate maps it to `{}`. Infra later migrates `staff_fiches.min_shift_hours` float → JSONB.

## Open Questions

None.
