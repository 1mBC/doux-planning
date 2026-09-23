# Proposal

## Why

Operators launch and export the banc from two pages (Banc IA / Banc Manuels). HTTP must keep enqueue and export on the origin of the page so Banc IA never queues imported games. File 73 freeze (`contracts/domain/admin-ui-pass.md` Infra) lands after file 72 (tombstones). No Core.

## What Changes

- SPA `SPA_PATHS` includes `/admin/bench/manuels` (same `index.html` fallback as `/admin/bench`).
- `POST /v1/admin/bench/run` optional body `origin`: `"catalogue"` | `"imported"`. Absent / `null` / `""` = both origins (compat). Anything else → 400 `Champs invalides.`
- Filter `_known_targets` / `_gap_targets` / `_all_listings` for `scope=all` | `category` | `gaps`. `scope=dataset` ignores `origin`. Category + origin mismatch → empty list, not 400.
- `GET /v1/admin/bench/export` optional query `origin`, same semantics for `below_manuel` and `bank`. `scope=dataset` ignores origin.
- `GET /versions` unchanged. Tombstones still excluded. Cuisine-only imported still 400 on dataset and skipped in all/gaps. No Alembic. DELETE / import / impersonate untouched.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `build-planning-api`: optional `origin` on bench run and export; SPA `/admin/bench/manuels`.

## Impact

- Infra only: `src/doux_planning/api/app.py`, `src/doux_planning/api/bench.py`, TestClient (`skipif` without `DATABASE_URL`).
- Do not edit `web/`, Core outside `api/`, `contracts/`, `engine.py` formulas, or `data/bench/`.
- No archive/sync. No Core rewrite.
