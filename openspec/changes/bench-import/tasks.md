# Tasks

## 1. Extract solve

- [x] 1.1 Extract `run_bench_on(dataset, effort, engine_ref=None)` from the current `run_bench` body (salle-only, no `published_cycles` write, evaluate expected, deltas, trace) and make `run_bench` load then delegate; verify `run_bench_on(load_bench_dataset("tight","halles"), MINIMAL)` matches `run_bench(...)` on category, id, effort, engine_ref, assignment count, score.global, expected_score.global
- [x] 1.2 Add `bench_dataset_from_json(*, category, id, name, challenge_fr, context, assignments)` reusing `_load_context` and `_shift`, omit employee `invite_token`, export both helpers from `doux_planning.bench`; verify `assignments=[]` returns empty expected without raising

## 2. Catalogue guard

- [x] 2.1 Keep `load_bench_dataset` / `list_bench_datasets` behaviour and do not rewrite `data/bench/` files; verify `list_bench_datasets` still has 50 entries and Core pytest for the new tests is green

## 3. Persist import

- [x] 3.1 Alembic after `20260922_0017`: table `bench_imported_datasets` (`category`, `id` PK, `name`, `challenge_fr`, `comment` nullable, `origin`, `source_restaurant_id` nullable, `context` JSONB, `expected` JSONB, `manual_score_override` Float nullable, `created_at`); SQLAlchemy model. Verify `alembic upgrade head`

## 4. HTTP

- [x] 4.1 `GET /v1/admin/restaurants/{restaurant_id}/import-preview` Bearer admin returns ready / manuel_published / computes_published / generate_count. Verify flags; 404 `Restaurant introuvable.`; 403 admin; 401/503 like file 70
- [x] 4.2 `POST /v1/admin/bench/import` snapshots checked teams (no `invite_token`), optional manuel union + override, optional salle `bench_runs` from published computes. Verify 200 body; both teams false / bad score → 400 `Champs invalides.`; unknown resto 404. Live restaurant unchanged
- [x] 4.3 `GET /versions` catalogue then imported with `origin` and `comment`; load imported via `bench_dataset_from_json`; worker disk-miss → DB → `run_bench_on`; persist override overwrites `expected_score.global` + `deltas.global`; export JSONB context; cuisine-only POST dataset → 400 `Ce jeu n’a pas de salle.`; gaps skip those. Verify halles still disk; include_runs last-run without POST run; cuisine-only 400

## 5. Tests

- [x] 5.1 TestClient coverage (`skipif` without `DATABASE_URL`) for preview flags, import + override `manual.global`, include_runs last-run, cuisine-only 400, 403/404, catalogue halles from disk. Do not fix pre-existing Saint-Cloud / engine-ref failures. Verify new tests green
