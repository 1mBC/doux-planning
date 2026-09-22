# Proposal

## Why

Infra will persist imported restaurants as in-memory bench games (no git catalogue rewrite). Core must solve and hydrate a `BenchDataset` that never lived on disk, without changing the 50-file catalogue or the disk `run_bench` calling shape.

## What Changes

- Extract `run_bench_on(dataset, effort, engine_ref=None)` from the current `run_bench` body (salle-only employees/structures, no `published_cycles` writes, evaluate expected, deltas, trace).
- `run_bench(category, id, effort, engine_ref=None)` loads from disk then delegates to `run_bench_on`. Outcome on a catalogue game stays the same (stable fields).
- Add `bench_dataset_from_json(*, category, id, name, challenge_fr, context, assignments)` reusing `_load_context` and `_shift`. `assignments` may be `[]`. Ignore `invite_token` on employees.
- Export both from `doux_planning.bench`. No Postgres, no HTTP, no `data/bench/` rewrites.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `bench-datasets`: a bench game can be built from JSON (empty oracle OK) and solved via `run_bench_on` without reading disk.

## Impact

- `src/doux_planning/bench.py` and Core tests under `tests/`.
- Do not edit `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, or `data/bench/` files.
- Infra HTTP/import tables stay out of this slice.
