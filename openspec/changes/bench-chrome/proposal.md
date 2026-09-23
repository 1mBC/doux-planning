# Proposal

## Why

Operators need to drop a bench game and all of its results from the admin banc. Catalogue files stay in git so a Railway redeploy does not resurrect a deleted game: Infra stores a tombstone instead. File 72 freeze (`contracts/domain/bench-chrome.md` Infra) lands after file 71 (`origin`, imported rows).

## What Changes

- Alembic table `bench_tombstones` (`category`, `dataset_id`, `created_at`, PK couple) after `20260922_0018`.
- `DELETE /v1/admin/bench/datasets/{category}/{dataset_id}` Bearer admin → 204.
- Imported (`category=imported` and row exists): DELETE `bench_imported_datasets` row plus all `bench_runs` and `bench_jobs` for that couple.
- Catalogue (files on disk): do not delete files. INSERT tombstone. DELETE runs + jobs. Second DELETE is 204 if already tombstoned.
- Unknown (not on disk, not imported, not tombstone) → 404 `Jeu introuvable.`
- 403 `Action réservée à l’admin.` 401 session. 503 no DB.
- `GET /versions`, `list_datasets`, export, `scope=all`, `scope=category`, `gaps`, `_known_targets` exclude tombstones. Imported rows that were not deleted stay listed. No new JSON keys (`origin` already from file 71).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `build-planning-api`: admin can delete a bench dataset (imported drop vs catalogue tombstone) and listing/enqueue/export paths omit tombstones.

## Impact

- Infra only: `src/doux_planning/api/` (bench, db, app) + Alembic + TestClient (`skipif` without `DATABASE_URL`).
- Do not edit `web/`, Core outside `api/`, `contracts/`, `engine.py` formulas, or `data/bench/` files (never delete catalogue JSON).
- No archive/sync. No Core rewrite.
