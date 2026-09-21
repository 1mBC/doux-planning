# Tasks

## 1. Fiche map

- [x] 1.1 Change `Employee.min_shift_hours` to a sparse `Mapping[str, float]`, add `min_shift_for`, reject values ≤ 0 with the existing `ValueError`, reject unknown keys, freeze the map, and verify empty map / missing key / unknown service return 4
- [x] 1.2 Hydrate and bench JSON: number 4 or omitted → `{}`; other N → N on that draft’s company services; mapping stored sparse; no `continuous` keys; do not rewrite `data/examples/saint-cloud.json`; verify numeric 3 on a midday+evening draft

## 2. Engine and sandbox

- [x] 2.1 In `engine.py` and every `engines/*.py` `_assigned_window` that calls `stretch_to_min_shift`, pass `min_shift_for(employee, structure.service_id)` (do not edit `stretch_to_min_shift` body) and verify evening `{"evening": 3}` stretches to 3 h while midday stays 4 h
- [x] 2.2 Use `min_shift_for` in sandbox `preview_retune`, `preview_fill`, and `_fill_hours` for that slot’s `service_id`, and verify duration checks follow the per-service minimum
- [x] 2.3 Adapt `test_lower_personal_min_shift_fills_a_short_post` to the mapping and keep Saint-Cloud pytest green

## 3. HTTP API (`build-planning-api`)

- [ ] 3.1 Alembic after `20260921_0015`: `staff_fiches.min_shift_hours` Float → JSONB (`4` → `{}`; other N → `{"morning":N,"midday":N,"evening":N}`), update `StaffFiche.min_shift_hours`, and verify `_fiche_to_employee` / persist use Core `coerce_min_shift_hours` (mapping, not `float`)
- [ ] 3.2 GET `employees[].min_shift_hours` as an object with one key per offered company service (`min_shift_for`, default 4, never a number). PATCH / import: object (sparse OK) or number (`4` → `{}`; other N → offered services or the three keys). Invalid key / ≤ 0 → 400 `Champs invalides.` Export uses serialize_context employees without `invite_token`. PATCH `services` that unchecks a service drops that key from every fiche map before persist
- [ ] 3.3 TestClient coverage (`skipif` without `DATABASE_URL`): PATCH `{ "min_shift_hours": { "evening": 3.5 } }` on midday+evening → GET evening 3.5 / midday 4; PATCH number `4` → GET object of 4s for offered services; invalid key / 0 → 400; uncheck morning → that key gone on employees; existing context/auth tests green
