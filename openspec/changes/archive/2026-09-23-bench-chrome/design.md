# Design

## Context

See proposal.md. File 71 already persists `bench_imported_datasets` and emits `origin` on `/versions`. Listing goes through `_all_listings()` (catalogue disk order then imported `created_at` desc). Core `list_bench_datasets` stays disk-only. Freeze Infra of `contracts/domain/bench-chrome.md` wins. Do not edit `contracts/`.

## Goals / Non-Goals

**Goals:**
- Table `bench_tombstones` after `20260922_0018`.
- DELETE imported vs catalogue vs unknown as in the freeze.
- Filter tombstones in `_all_listings` (covers `/versions`, export, all/category/dataset known targets, gaps) and in `list_datasets`.
- HTTP 204 / 404 `Jeu introuvable.` / 403 / 401 / 503.

**Non-Goals:**
- Core rewrite (`run_bench_on`, `list_bench_datasets`, catalogue JSON).
- UI (`web/`), contracts, engine formulas.
- Archive / sync.
- Cuisine solve. Editing an imported game.

## Decisions

### 1. Filter at `_all_listings`, not Core

`list_bench_datasets` keeps returning fifty disk games. API subtracts tombstone keys so a Railway redeploy that still has the git files does not list a deleted game.

### 2. Imported delete is a hard drop; catalogue is a tombstone

Imported ids are opaque `imp-…` rows. Drop the row + runs + jobs. A second DELETE is 404 (no row, not on disk, not tombstoned). Catalogue must survive git; INSERT tombstone and purge results; second DELETE 204.

### 3. Existence checks in that order

1. `category=imported` and imported row exists → drop.
2. Tombstone already present → purge results (noop) → 204.
3. Catalogue files on disk (`context.json` + `expected.json`) → insert tombstone + purge → 204.
4. Else 404.

### 4. Tests restore the halles tombstone

Shared Postgres: DELETE `tight/halles` would hide it for later modules (`test_bench_import` asserts halles on `/versions`). The halles test removes the tombstone row in a `finally` so other files still see the catalogue game. Files on disk are never deleted.

## Risks / Trade-offs

- [Shared test DB hides halles for later tests] → restore the tombstone row after assertions.
- [POST gaps inserts many jobs] → still POST `scope=gaps` and assert no job is `tight`/`halles`.
- [Pre-existing Saint-Cloud / engine-ref pytest failures] → leave them.

## Migration Plan

`alembic upgrade head` after `20260922_0018` creates `bench_tombstones`. Rollback drops the table. Catalogue files unchanged.

## Open Questions

None.
