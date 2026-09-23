# Spec Delta

## ADDED Requirements

### Requirement: Context employees expose per-service min shift hours
`GET /v1/context` `employees[].min_shift_hours` SHALL be an object with **one key per offered company service** (`morning` | `midday` | `evening` present on the restaurant). Each value MUST be Core `min_shift_for` (missing key → 4). The field MUST NEVER be a JSON number. `GET /v1/context/export` MUST emit the same employee field (without `invite_token`). Persist MUST store a JSONB mapping on `staff_fiches.min_shift_hours`, not a float. `_fiche_to_employee` MUST pass the mapping through Core `coerce_min_shift_hours`.

#### Scenario: Sparse evening override fills midday default
- **WHEN** a restaurant offers midday and evening and a fiche is patched with `{ "min_shift_hours": { "evening": 3.5 } }`
- **THEN** GET returns `evening` 3.5 and `midday` 4 as an object (never `3.5` or `4` as a number)

#### Scenario: Number 4 becomes the default object
- **WHEN** a restaurateur patches `min_shift_hours` as the number `4`
- **THEN** GET returns an object of 4s for each offered service

### Requirement: PATCH and import coerce min shift hours
`PATCH /v1/context` and `POST /v1/context/import` SHALL accept `min_shift_hours` as a sparse object **or** a number. Coercion MUST use Core `coerce_min_shift_hours` (number `4` → `{}`; other N → offered services when present, else the three company keys). A key outside `morning|midday|evening` or a value ≤ 0 MUST be HTTP 400 `Champs invalides.`

#### Scenario: Invalid key is 400
- **WHEN** PATCH sends `min_shift_hours` with a `continuous` key or a value `0`
- **THEN** the response is 400 `Champs invalides.`

### Requirement: Unchecking a service drops min-shift keys
When `PATCH /v1/context` replaces `services` and a previously offered service is removed, persist MUST drop that key from **every** fiche `min_shift_hours` map before write (same smash as unavail / `max_services`). A later GET MUST NOT emit the dropped service.

#### Scenario: Uncheck morning
- **WHEN** morning is unchecked after a fiche had a morning min-shift key
- **THEN** GET employees no longer include `morning` on `min_shift_hours`
