# Design

## Context

See proposal.md. `run_bench` in `src/doux_planning/bench.py` loads a disk dataset then generates salle-only against the oracle. Infra passes a snapshot that never existed under `data/bench/`. Freeze Core + Infra of `contracts/domain/bench-import.md` wins. `_load_context` already hydrates multi-team JSON; `_employee` already omits `invite_token`. File 70 restaurant GET style (`404 Restaurant introuvable.`, admin 403/401/503) is reused for preview.

## Goals / Non-Goals

**Goals:**
- One in-memory solve entry (`run_bench_on`) shared by disk `run_bench` and imported rows.
- JSON → `BenchDataset` without touching the catalogue scanner.
- Table `bench_imported_datasets`; preview + POST import; versions catalogue then imported with `origin`/`comment`.
- Worker: disk miss → DB → `run_bench_on`. Override overwrites persisted `expected_score.global` and `deltas.global`.
- Cuisine-only dataset: POST `scope=dataset` → 400 `Ce jeu n’a pas de salle.`; gaps skip.

**Non-Goals:**
- Rewriting `load_bench_dataset` / `list_bench_datasets` or any `data/bench/` file.
- DELETE / `bench_tombstones` / chrome filter (file 72).
- Cuisine solve on the bench.
- UI (`web/`), contracts, engine formulas.

## Decisions

### 1. Extract the current body, keep `run_bench` as a thin load wrapper

Move the generate/evaluate block into `run_bench_on(dataset, effort, engine_ref=None)`. `run_bench` calls `load_bench_dataset` then `run_bench_on`. Infra `resolve_bench_dataset` tries disk then DB and calls `run_bench_on` (does not rewrite Core).

### 2. Hydrate JSON with `_load_context` + `_shift`

`bench_dataset_from_json` keyword-only args match the freeze. Expected `[]` is `()`. Dataset `name` / `challenge_fr` are the kwargs.

### 3. Imported rows are a fourth listing source, not a catalogue rewrite

`list_bench_datasets` stays disk-only. HTTP `_all_listings` = catalogue order then imported `created_at` desc. Category of imported games is always `imported`. `POST` `scope=category` with `category=imported` is allowed even though `BENCH_CATEGORY_ORDER` stays Core-frozen.

### 4. Snapshot is filtered to checked teams

Hours / types / typical_week / roles / employees keep only `include_salle` / `include_cuisine` teams. No `invite_token`. Name = trimmed `companies.name`, else restaurateur email, else `Sans nom`. `challenge_fr` = comment if present else `Importé de {email}`.

Oracle: if `include_manuel` and at least one checked team has `versions.manuel` → union of those assignments (team-filtered). Else `expected.assignments = []`.

`include_runs`: salle slots only, and only if `include_salle`. Insert `bench_runs` (trace null; `engine_ref` from slot or `get_effective_engine_ref`; duration from slot or 0). No cuisine `bench_runs`.

### 5. Manuel column and persist override

`GET /versions` `dataset.manual.global`:

1. `manual_score_override` if set (even before any run)
2. else evaluate expected if non-empty (null before first run, same as catalogue)
3. else null

On persist of `run_bench_on`: if override, overwrite `expected_score.global` and recompute `deltas.global`. Empty expected + override on copied runs → `{ global: override, notes: 5× null, weights }`.

### 6. Tests compare stable outcome fields only (Core)

Two independent generates may differ in `duration_seconds`. Infra tests are TestClient `skipif` without `DATABASE_URL`. Do not “fix” pre-existing Saint-Cloud / engine-ref failures.

## Risks / Trade-offs

- [POST all total] → catalogue still 50; imported rows are extra. Existing HTTP tests run before this file’s tests in collection order.
- [Cuisine-only enqueue] → 400 on dataset; skip in all/category/gaps so the worker never solves an empty salle.
- [Pre-existing Saint-Cloud / engine-ref pytest failures] → leave them.

## Migration Plan

`alembic upgrade head` after `20260922_0017` creates `bench_imported_datasets`. Rollback drops the table. Catalogue files unchanged.

## Open Questions

None.
