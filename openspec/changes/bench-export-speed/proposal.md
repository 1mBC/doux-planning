# Proposal

## Why

Banc Manuels « Exporter ce jeu » 404s when the last-run is a copied import under a restaurant `engine_ref` other than VERSION. `GET /versions` also loads the full catalogue plus imported JSONB on every Banc Manuels visit. File 74 freeze (`contracts/domain/bench-export-speed.md` Infra) wins over `bench.md` `scope=dataset` / GET `/versions` and completes `admin-ui-pass.md` (`origin` already on run/export). No Core.

## What Changes

- `GET /v1/admin/bench/export?scope=dataset` exports last-runs of **all** `engine_ref` for that game (same shape as `scope=bank` for one row). Reuse `_latest_runs_by_quad` + `_bank_pack_entry`. Stop using `_latest_current_runs_map` here. `below_manuel` stays VERSION-only.
- Unknown listing → 404 `Jeu introuvable.` Listing exists, zero `bench_runs` → 404 `Aucun run pour ce jeu.` Copied import runs (`trace=null`) count if they are the last-run of that (ref, effort). Query `origin` still ignored on dataset.
- `GET /v1/admin/bench/versions?origin=catalogue|imported`. Absent / `null` / `""` → both origins (Stats). Unknown → 400 `Champs invalides.`
- `catalogue`: disk listings only; SQL `bench_runs.category != 'imported'`. Do not call `list_imported_rows` / load imported context.
- `imported`: imported listings only; SQL `category = 'imported'`. Do not walk `data/bench/**`.
- Versions cells: `load_only` / targeted SELECT — do not load `assignments`, `warnings`, `trace`, nor `bench_imported_datasets.context`.
- `engine_refs` = full `list_engine_refs()` ∪ extras from **filtered** runs. No Alembic.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `build-planning-api`: dataset export is all last-run engines; `GET /versions` accepts `origin` and loads light cells.

## Impact

- Infra only: `src/doux_planning/api/app.py`, `src/doux_planning/api/bench.py`, `src/doux_planning/api/bench_import.py`, TestClient (`skipif` without `DATABASE_URL`).
- Do not edit `web/`, Core outside `api/`, `contracts/`, `engine.py` formulas, or `data/bench/`.
- No archive/sync. No Core rewrite. DELETE / import / impersonate / POST run origin semantics unchanged.
