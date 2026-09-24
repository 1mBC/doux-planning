# Design

## Context

See proposal.md for why. `list_engine_refs()` already is the registry, last name today `mix-0`. `GET /v1/admin/bench/versions` returns `engine_ref` from `data/bench/VERSION` (`core-5`) plus `engine_refs`. The picklist is React state seeded from that field. `live_engine` is a separate one-row table; its empty or unknown value still falls back to `VERSION`. Gap fill already walks the whole registry.

## Goals / Non-Goals

**Goals:**

- One global bench choice, resolved on read, shared by both bench pages.
- The restaurant choice keeps its own row and the same fallback rule.
- Unknown or missing stored name becomes the last registry name and is written back.
- `data/bench/VERSION` is gone. `core-5` stays the registry name of live `engine.py`.

**Non-Goals:**

- A database catalogue of engines.
- One shared row for the bench and the restaurant.
- Passing the stored bench choice into gap fill.
- Moving a stored choice when a later change appends an engine. Only a missing or unknown name jumps to the new last.

## Decisions

1. **New one-row table `bench_engine`**, same shape as `live_engine` (`id`, `engine_ref` text nullable). Not a column on `live_engine`. The two choices must be able to differ.
   Alternative: reuse `live_engine`. Rejected: picking a bench engine would change restaurant generate.

2. **Same resolver for both rows.** If the row is missing, null, blank, or not in `list_engine_refs()`, set `engine_ref` to `list_engine_refs()[-1]` and return that. Bench resolver feeds versions, omitted run, path compare, and `below_manuel`. Restaurant resolver feeds `GET/PUT /v1/admin/live-engine` and generate. The write happens on read so the next reload matches.
   Alternative: compute the fallback only in the response and leave the bad row. Rejected: a later registry change that reintroduces the old name would silently restore it.

3. **`PUT /v1/admin/bench/engine`** body `{ "engine_ref": "<id>" }`. Admin only. Unknown, empty, or wrong type → 400 `Moteur inconnu.` and no write. 200 returns the same shape as the restaurant engine route: `{ engine_ref, engine_refs }` where `engine_ref` is the stored name and `engine_refs` is the registry only (not the union with extra run names).
   The versions payload keeps its existing `engine_refs` union. Its `engine_ref` becomes the resolver result.
   Alternative: save only by posting a run. Rejected: a pick must stick before any launch.

4. **`POST /v1/admin/bench/run`**: present and valid `engine_ref` is that launch only. Absent or empty uses the resolver. Present and invalid stays 400 `engine_ref inconnu` and does not change the stored choice.
   Gap scope keeps ignoring `engine_ref`.

5. **UI** calls `PUT` when a select changes. Bench: `PUT /v1/admin/bench/engine`. Restaurant: the existing `PUT /v1/admin/live-engine`. On success, the select shows the stored name. On failure, it stays on the previous effective name and the page shows the API `detail`. Reload does not keep a private selection that disagrees with `GET`. Neither screen hardcodes a default engine name.

6. **Core deletes `data/bench/VERSION` and stops reading it.** `engine_ref()` goes away. A domain call with no engine (`generate_team`, `run_bench`) uses `list_engine_refs()[-1]`. `core-5` stays mapped to `engine.py` inside the registry. Infra does not read the file either.

## Risks / Trade-offs

- [Read-path write] A `GET` that repairs an unknown name writes the database. → Same admin-only routes already require a database; without `DATABASE_URL` they stay 503 and do not pretend a choice exists.
- [Default moves from `core-5` to `mix-0`] A bench or a restaurant that never stored a valid engine will use `mix-0` after deploy. → Intended. Old runs and old published cycles stay under the engine that produced them.
- [Shared choice] Two admins overwrite each other, separately for the bench and for the restaurant. → One product, one choice per picker.
- [Appending an engine] The new last name becomes the fallback, not the stored choice. → Installs that already persisted `mix-0` stay there until someone picks again.

## Migration Plan

Core removes `data/bench/VERSION` in the same release as the API change. Alembic after `20260922_0019` creates `bench_engine`. No backfill on either row. First read of each row inserts the last registry name. Rollback needs the file and the old fallback restored together. Dropping the table alone is not enough.

## Open Questions

None.
