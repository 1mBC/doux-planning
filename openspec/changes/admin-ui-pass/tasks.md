# Tasks

## 1. HTTP + SPA

- [x] 1.1 Add `/admin/bench/manuels` to `SPA_PATHS` in `src/doux_planning/api/app.py`. Optional `origin` (`catalogue` | `imported`) on `POST /v1/admin/bench/run` (filter all / category / gaps) and `GET /v1/admin/bench/export` (below_manuel / bank). Absent / null / `""` = both origins. Unknown → 400 `Champs invalides.` `scope=dataset` ignores origin. Category + origin mismatch → empty, not 400. Tombstones and cuisine-only unchanged. Wire the export query on `admin_bench_export`. Verify TestClient (`skipif` without `DATABASE_URL`): SPA manuels index if dist (skip otherwise); after import all+catalogue no imported jobs, all+imported no catalogue, gaps+catalogue no imported; no origin both; origin=nope 400; export bank&origin=catalogue no imported; 403 non-admin. Do not fix pre-existing Saint-Cloud / engine-ref failures. No `web/` / Core outside `api/` / `contracts/` / `engine.py` / `data/bench/`
