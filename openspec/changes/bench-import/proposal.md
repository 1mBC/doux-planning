# Proposal

## Why

Infra will persist imported restaurants as in-memory bench games (no git catalogue rewrite). Core must solve and hydrate a `BenchDataset` that never lived on disk, without changing the 50-file catalogue or the disk `run_bench` calling shape. File 71 then snapshots a live restaurant into Postgres (`bench_imported_datasets`) and lists it next to the catalogue.

## What Changes

- Extract `run_bench_on(dataset, effort, engine_ref=None)` from the current `run_bench` body (salle-only employees/structures, no `published_cycles` writes, evaluate expected, deltas, trace).
- `run_bench(category, id, effort, engine_ref=None)` loads from disk then delegates to `run_bench_on`. Outcome on a catalogue game stays the same (stable fields).
- Add `bench_dataset_from_json(*, category, id, name, challenge_fr, context, assignments)` reusing `_load_context` and `_shift`. `assignments` may be `[]`. Ignore `invite_token` on employees.
- Export both from `doux_planning.bench`. Core does not add Postgres or HTTP.
- Alembic table `bench_imported_datasets` (category always `imported`). Reuse `bench_runs` / `bench_jobs`.
- `GET /v1/admin/restaurants/{id}/import-preview` and `POST /v1/admin/bench/import` (Bearer admin).
- `GET /v1/admin/bench/versions` lists catalogue then imported (`created_at` desc) with required `origin` and `comment`. Worker/export/POST run load imported from JSONB via `bench_dataset_from_json` + `run_bench_on`. Cuisine-only import → 400 `Ce jeu n’a pas de salle.` Gaps skip those. No DELETE (file 72).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `bench-datasets`: a bench game can be built from JSON (empty oracle OK) and solved via `run_bench_on` without reading disk.
- `build-planning-api`: persist an imported restaurant as a bench dataset, preview flags, versions `origin`/`comment`, worker DB fallback, export JSONB context.

## Impact

- Core: `src/doux_planning/bench.py` and Core tests under `tests/`.
- Infra: `src/doux_planning/api/` (bench, worker, db, app) + Alembic after `20260922_0017` + TestClient (`skipif` without `DATABASE_URL`).
- Do not edit `web/`, `contracts/`, `engine.py` formulas, or `data/bench/` files. File 72 (DELETE / tombstones) stays out of this slice.
