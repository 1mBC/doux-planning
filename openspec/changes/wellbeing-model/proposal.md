## Why

Wellbeing is still a bag of enum flags and leftover evening/morning caps. The restaurateur needs one structured fiche (consecutive rest, weekend radio, per-service caps, coupure cap including 0) and the engine must score and solve that model. Old keys must be refused.

## What Changes

- Replace `WellbeingPreference` frozenset with `Wellbeing { consecutive_rest, weekend, max_services, max_coupures_per_week }`.
- `Unavailability` is only `{ weekday, service_id }`. Drop `every_morning` / `every_evening`.
- `week_label_scheme(state)` → `"parity"` if any fiche has weekend even/odd, else `"ab"`.
- Engine warnings and rest/fill solver follow the freeze (consecutive rest per week with closed days, weekend even/odd/every_two, max morning/midday/evening, max coupures including 0). Fill **refuses** a shift that would exceed a posed `max_services` cap (same week counter as evaluate) — ineligible like an overlap, not a late tie-break. Absent key = no cap. Evaluate / facts stay souhait. Legal formulas unchanged.
- Fill and hole-repair walk windows in **`fewest`** order (`core-2`): fewest statically eligible people first (empty board + rest + indispos + hard caps + legal), then `day_index`, restaurant service order, post level descending. Not `weekend-eve` / `eve-first`.
- `generate_cycle` (`core-3`) runs seeders → SAT constrained by locks → fill holes (locks frozen) → keep-best. Five seeders: `tight-frozen`, `tight-dynamic`, `high-role`, `weekend-scarce`, `empty` (×1). `SEED_TIGHT_THRESHOLD = 3`. Infeasible locked SAT is discarded (no slack).
- Fill `_soft_penalty` drops `int(not started_day)` and instead penalizes creating a same-day coupure. Fewest-first stays.
- Hydrate accepts the new form only and refuses deleted keys.
- `employee_board.wishes` becomes `{ kind, held, … }` from posed wishes. Board still reads the published result only.
- Adapt `data/examples/saint-cloud.json` employees. Rewrite `planning` only if generate_cycle output changes; report new stats, do not edit the example HTTP contract.
- `data/bench/VERSION` = `core-3` (`engine_ref()`).
- No HTTP, no `web/`, no `api/`, no `contracts/` edits. Catalogue 50 games stay bit-identical.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: wellbeing model, indispos jour×service, week labels, and employee-board wish rows.

## Impact

- `staff.py`, `types.py`, `engine.py` (warnings + rest/fill aims + fewest window order + seeders/SAT locks + anti-coupure fill), `context.py` (`week_label_scheme`, board wishes), `hydrate.py`, `data/examples/saint-cloud.json`, `data/bench/VERSION`.
- Tests: freeze scenarios + domain / engine / hydrate / employee_board / generate / bench. HTTP `api/` may fail on old `wellbeing: []` — list, do not patch.
