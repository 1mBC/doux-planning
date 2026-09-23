## Why

A published cycle needs a live recap (stats, legal table, wish table) read from the stored result — not a second solve, and not Saint-Cloud’s dead `we1j` / `weA` columns. The 11 h rest warning must show both clocks so the restaurateur can see the gap.

## What Changes

- Add `cycle_recap(state, team) -> CycleRecap` over `published_cycles[team]`. Empty → `NoPublishedCycle`. No `generate_cycle`.
- Stats, `legal_*`, and `wish_*` follow the live freeze (new wish keys, not snapshot aliases).
- Enrich `evaluate` `rest_between_days` message in French with `{jourA} {fin} → {jourB} {début}`. `day_index` stays day A. Do not translate other codes.
- Do not rewrite `data/examples/saint-cloud.json`. No HTTP, no `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: published-cycle recap and 11 h rest warning clocks.

## Impact

- `context.py` (`cycle_recap`), `engine.py` (`rest_between_days` message). Tests for freeze scenarios. Do not edit `web/`, `api/`, `contracts/`, or the Saint-Cloud snapshot.
