# Tasks

## 1. Persist

- [x] 1.1 Alembic after `20260922_0018`: table `bench_tombstones` (`category`, `dataset_id`, `created_at`; PK `(category, dataset_id)`); SQLAlchemy model. Verify `alembic upgrade head`

## 2. HTTP

- [x] 2.1 `DELETE /v1/admin/bench/datasets/{category}/{dataset_id}` Bearer admin → 204. Imported: drop `bench_imported_datasets` row + all `bench_runs` + `bench_jobs` for that couple. Catalogue: INSERT tombstone, drop runs+jobs, do not delete files; 2nd DELETE 204. Unknown → 404 `Jeu introuvable.` Non-admin → 403 `Action réservée à l’admin.` Missing session → 401. No DB → 503. Verify TestClient skipif without `DATABASE_URL`
- [x] 2.2 `_all_listings` / `list_datasets` / export / `scope=all` / `scope=category` / `gaps` / `_known_targets` exclude tombstones; imported (not deleted) still listed. Verify `/versions` omits tombstoned halles; POST gaps does not enqueue halles; catalogue folder still on disk

## 3. Tests

- [x] 3.1 TestClient coverage (`skipif` without `DATABASE_URL`): import then DELETE gone from `/versions` with 0 runs/jobs; DELETE `tight/halles` not listed, files remain, 2nd DELETE 204; gaps skip halles; unknown 404 `Jeu introuvable.`; non-admin 403. Do not fix pre-existing Saint-Cloud / engine-ref failures. Verify new tests green
