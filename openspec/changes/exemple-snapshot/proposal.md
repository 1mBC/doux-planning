## Why

The public Saint-Cloud file still ships English warning messages and dead wish columns (`we1j` / `weA`). `/exemple` must read like the live recap without a second solve.

## What Changes

- Rewrite `data/examples/saint-cloud.json` `planning.warnings`, `stats`, `legal_rows`, `wish_cols`, and `wish_rows` from `evaluate` + salle `cycle_recap` on the file’s restaurant + assignments.
- Keep `restaurant`, `assignments`, `search_effort` / `calendars` / `seconds` unchanged. Do not call `generate_cycle`. Do not add `legal_cols`.
- Wish columns use live keys (no `we1j` / `weA` / `weB` / `soirs` / `repos2` / `coupures`). Warning messages are French.
- Keep 92 shifts, Théo 11h–16h, Diane `30h · 29h / 39h`. No `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: public Saint-Cloud snapshot recap matches live evaluate + salle `cycle_recap`.

## Impact

- `data/examples/saint-cloud.json` recap blocks; optional refresh helper next to hydrate. Tests for freeze invariants. Do not edit `web/`, `api/`, or `contracts/`.
