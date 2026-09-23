# Design

## Context

See proposal.md. File 71 already emits `origin` on `/versions` and persists imported rows. File 72 filters tombstones in `_all_listings()`. Freeze Infra of `contracts/domain/admin-ui-pass.md` wins. Do not edit `contracts/`.

## Goals / Non-Goals

**Goals:**
- SPA `/admin/bench/manuels` served as `index.html` when `web/dist` exists.
- Optional `origin` on POST run (all / category / gaps) and GET export (below_manuel / bank).
- Catalogue = listings that are not imported (`category != imported`). Imported = `category=imported`.
- Unknown origin → 400 `Champs invalides.` Dataset scope ignores a present origin after validation.

**Non-Goals:**
- Core rewrite. UI (`web/`). Alembic. `/versions` query filter. DELETE / import / impersonate.

## Decisions

### 1. Filter at `_all_listings(origin)`, not Core

`list_bench_datasets` stays disk-only. API subtracts tombstones then optionally keeps catalogue or imported listings. `_known_targets` and `_gap_targets` pass the same `origin`. `list_versions` still calls `_all_listings()` with no origin.

### 2. Parse origin once

Allowed: `"catalogue"` | `"imported"`. Absent / `null` / `""` → `None` (no filter). Any other value → 400. Dataset run and dataset export still 400 on a bad origin, then ignore a valid one.

### 3. Empty mismatch is empty, not 404

`scope=category` + origin that does not cover that category returns the current empty enqueue path (`202` `total: 0`). Gaps with zero holes stay `200` `total: 0`.

## Risks / Trade-offs

- [POST all still inserts many catalogue jobs] → tests inspect `job_ids` / `BenchJob.category` without ticking.
- [Pre-existing Saint-Cloud / engine-ref pytest failures] → leave them.

## Migration Plan

None. No Alembic.

## Open Questions

None.
