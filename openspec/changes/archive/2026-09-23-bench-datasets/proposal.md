## Why

The restaurateur (admin) needs the salle bench catalogue on disk (50 games: challenge families plus 26 crafted oracles) so generation can be scored against a human oracle without touching a live restaurant, `published_cycles`, or keep-best.

## What Changes

- Add `list_bench_datasets`, `load_bench_dataset`, `run_bench`, and `UnknownBenchDataset`.
- Scan `data/bench/{category}/{id}/` ; omit a dataset that lacks both JSON files.
- Load as live context (`set_services`, ladder, types, typical week from JSON when present else derived 1 type per service, fiches). `team_ready(salle)` is true; cuisine is absent.
- Widen the on-disk catalogue to the 30 freeze pairs (7 existing files bit-identical). Categories add `hours`, `size`, `overqual`, `closed`, `shapes`. Morning service, several types per `service_id`, roles through L6. `VERSION` stays `core-2`.
- Add 20 planning-first `crafted` oracles (grille 14 j then deduced context). The 30 existing folders stay bit-identical. Each new oracle: 0 `interdit`, 0 `hours_miss`, 0 `below_role`, `cycle_score` ≥ 9.5. `VERSION` stays `core-2`.
- `run_bench` uses a disposable copy, `generate_for` (live or vendored) + recap ×2, and `deltas`. Optional `engine_ref` (omitted = `VERSION`). `BenchOutcome.trace` is always a `SearchTrace`. Zero writes to `published_cycles`.
- Vendored `engines/core_0.py` / `core_1.py` / `core_2.py` plus live `engine.py` (`core-3`). `list_engine_refs()` / `generate_for` / `UnknownEngineRef`. `VERSION` stays `core-3`.
- Do not persist `data/bench/VERSION` (Infra). Do not change `SEARCH_*`, `_attempt_key`, or `generate_cycle` keep-best / seeds.
- No HTTP, no `web/` / `api/` / `contracts/` / `data/bench/**` / `saint-cloud.json` edits. Catalogue 50 stays bit-identical.

## Capabilities

### New Capabilities

- `bench-datasets`: load the salle bench datasets from `data/bench/` (tight, clock, wishes, ladder, crafted, hours, size, overqual, closed, shapes) and run isolated generate vs oracle scores.

### Modified Capabilities

- (none)

## Impact

- `src/doux_planning/bench.py`, `src/doux_planning/engines/`, live `engine.py` trace bookkeeping, and tests. Do not edit `web/`, `api/`, `contracts/`, or rewrite the 50 dataset folders. `VERSION` stays `core-3`.
