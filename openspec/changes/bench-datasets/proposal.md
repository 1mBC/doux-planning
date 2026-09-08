## Why

The restaurateur (admin) needs four frozen salle datasets on disk so generation can be scored against a human oracle without touching a live restaurant, `published_cycles`, or keep-best.

## What Changes

- Add `list_bench_datasets`, `load_bench_dataset`, `run_bench`, and `UnknownBenchDataset`.
- Scan `data/bench/{category}/{id}/` ; omit a dataset that lacks both JSON files.
- Load as live context (`set_services`, ladder, types, derived typical week, fiches). `team_ready(salle)` is true; cuisine is absent.
- `run_bench` uses a disposable copy, `generate_cycle` + `cycle_score` twice (generated vs expected), and `deltas`. Zero writes to `published_cycles`.
- Do not persist `data/bench/VERSION` (Infra). Do not change `SEARCH_*`, `_attempt_key`, or `generate_cycle` keep-best.
- No HTTP, no `web/` / `api/` / `contracts/` / `data/bench/**` / `saint-cloud.json` edits.

## Capabilities

### New Capabilities

- `bench-datasets`: load the four salle bench datasets from `data/bench/` and run isolated generate vs oracle scores.

### Modified Capabilities

- (none)

## Impact

- New `src/doux_planning/bench.py` plus tests. Reuses `set_services` / `cycle_score` / `generate_cycle`. Do not edit `web/`, `api/`, `contracts/`, `engine.py` keep-best, or the bench JSON files.
