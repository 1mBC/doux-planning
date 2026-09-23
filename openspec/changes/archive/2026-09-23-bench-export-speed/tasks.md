# Tasks

## 1. HTTP

- [x] 1.1 `GET /v1/admin/bench/export?scope=dataset` uses last-runs of all `engine_ref` via `_latest_runs_by_quad` + `_bank_pack_entry` (or equivalent). Stop using `_latest_current_runs_map` for dataset; keep it for `below_manuel`. Unknown listing → 404 `Jeu introuvable.` Zero `bench_runs` → 404 `Aucun run pour ce jeu.` Copied import `trace=null` last-runs included. Query `origin` still ignored on dataset. No Alembic. No `web/` / Core outside `api/` / `contracts/` / `engine.py` / `data/bench/`
- [x] 1.2 Wire `GET /v1/admin/bench/versions?origin=` through `admin_bench_versions` → `list_versions(..., origin=)` with `_parse_origin`. `catalogue` / `imported` / absent as specified. Versions cells `load_only` / `defer` assignments, warnings, trace; imported metadata without `context`. `engine_refs` = `list_engine_refs()` ∪ extras from filtered runs. `_all_listings(origin)` skips the unused listing source

## 2. Tests

- [x] 2.1 TestClient coverage (`skipif` without `DATABASE_URL`): import resto with salle computes `engine_ref` ≠ VERSION, no VERSION re-run → dataset export 200 efforts non-empty with a non-VERSION `engine_ref`; catalogue 0 run → 404 `Aucun run pour ce jeu.`; `versions?origin=imported` has no catalogue; `origin=catalogue` has no imported; `origin=nope` → 400; no origin both; non-admin 403. Do not fix pre-existing Saint-Cloud / engine-ref failures. Verify new tests green
