# Tasks

## 1. Fiche map

- [ ] 1.1 Change `Employee.min_shift_hours` to a sparse `Mapping[str, float]`, add `min_shift_for`, reject values ≤ 0 with the existing `ValueError`, reject unknown keys, freeze the map, and verify empty map / missing key / unknown service return 4
- [ ] 1.2 Hydrate and bench JSON: number 4 or omitted → `{}`; other N → N on that draft’s company services; mapping stored sparse; no `continuous` keys; do not rewrite `data/examples/saint-cloud.json`; verify numeric 3 on a midday+evening draft

## 2. Engine and sandbox

- [ ] 2.1 In `engine.py` and every `engines/*.py` `_assigned_window` that calls `stretch_to_min_shift`, pass `min_shift_for(employee, structure.service_id)` (do not edit `stretch_to_min_shift` body) and verify evening `{"evening": 3}` stretches to 3 h while midday stays 4 h
- [ ] 2.2 Use `min_shift_for` in sandbox `preview_retune`, `preview_fill`, and `_fill_hours` for that slot’s `service_id`, and verify duration checks follow the per-service minimum
- [ ] 2.3 Adapt `test_lower_personal_min_shift_fills_a_short_post` to the mapping and keep Saint-Cloud pytest green
