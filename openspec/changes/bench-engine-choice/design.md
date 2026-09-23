# Design

## Context

See proposal.md for why. `list_engine_refs()` already is the registry, last name today `mix-0`. `GET /v1/admin/bench/versions` returns `engine_ref` from `data/bench/VERSION` (`core-5`) plus `engine_refs`. The picklist is React state seeded from that field. `live_engine` is a separate one-row table; its empty or unknown value still falls back to `VERSION`. Gap fill already walks the whole registry.

## Goals / Non-Goals

**Goals:**

- One global bench choice, resolved on read, shared by both bench pages.
- HTTP and UI agree on the same effective name.
- Unknown or missing stored name becomes the last registry name and is written back.

**Non-Goals:**

- A database catalogue of engines.
- Changing `live_engine`, `engine_ref()`, or the `VERSION` file.
- Passing the stored choice into gap fill.

## Decisions

1. **New one-row table `bench_engine`**, same shape as `live_engine` (`id`, `engine_ref` text nullable). Not a column on `live_engine`. The two choices must be able to differ.
   Alternative: reuse `live_engine`. Rejected: the restaurant fallback would follow the bench, which this change forbids.

2. **One resolver** used by versions, omitted run, path compare, and `below_manuel`. If the row is missing, null, blank, or not in `list_engine_refs()`, set `engine_ref` to `list_engine_refs()[-1]` and return that. The write happens on read so the next reload matches.
   Alternative: compute the fallback only in the response and leave the bad row. Rejected: a later registry change that reintroduces the old name would silently restore it.

3. **`PUT /v1/admin/bench/engine`** body `{ "engine_ref": "<id>" }`. Admin only. Unknown, empty, or wrong type → 400 `Moteur inconnu.` and no write. 200 returns the same shape as the restaurant engine route: `{ engine_ref, engine_refs }` where `engine_ref` is the stored name and `engine_refs` is the registry only (not the union with extra run names).
   The versions payload keeps its existing `engine_refs` union. Its `engine_ref` becomes the resolver result.
   Alternative: save only by posting a run. Rejected: a pick must stick before any launch.

4. **`POST /v1/admin/bench/run`**: present and valid `engine_ref` is that launch only. Absent or empty uses the resolver. Present and invalid stays 400 `engine_ref inconnu` and does not change the stored choice.
   Gap scope keeps ignoring `engine_ref`.

5. **UI** calls `PUT` when the select changes. On success, both the local selection and any later `GET /versions` show that name. On failure, the select stays on the previous effective name and the page shows the API `detail`. Reload does not keep a private selection that disagrees with `GET`.

6. **Core does no work.** Infra calls `list_engine_refs()` itself.

## Risks / Trade-offs

- [Read-path write] A `GET` that repairs an unknown name writes the database. → Same admin-only routes already require a database; without `DATABASE_URL` they stay 503 and do not pretend a choice exists.
- [Default moves from `core-5` to `mix-0`] Existing operators who never picked an engine will launch `mix-0` after deploy. → Intended. Old runs stay under their own `engine_ref`. `below_manuel` and path compare follow the new effective name, so they may 404 until that engine has a last-run.
- [Shared choice] Two admins overwrite each other. → One bench, one choice, same rule as `live_engine`.

## Migration Plan

Alembic after `20260922_0019` creates `bench_engine`. No backfill. First read inserts the last registry name. Rollback drops the table; bench current-engine routes fall back to today's `VERSION` behavior only if this change is reverted in code as well.

## Open Questions

None.
