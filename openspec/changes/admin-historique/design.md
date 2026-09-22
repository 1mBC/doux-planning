# Design

## Context

See proposal.md for motivation. Freeze: `contracts/domain/admin-historique.md` (wins) plus `admin.md` / `v1-auth.md`. Generate logs already exist; `_log_generate` already receives `restaurant_id`. Company `GET /v1/cycles` and `GET /v1/context` already serialize live published cycles and context. Sessions are opaque sha256 hashes with `SESSION_TTL` 30 days. SPA fallback already mounts parameterized `/admin/bench/run/{run_id}`.

## Goals / Non-Goals

**Goals:**
- Alembic after `20260921_0016` for nullable log columns (no FK on `restaurant_id`) plus `impersonate_tokens`.
- Reuse company serialize paths for admin GET cycles/context; 404 when the company row is missing (do not reuse `_load_company`’s 401).
- Hash impersonate opaques like session tokens; mint TTL 15 minutes; consume is one-shot and issues a new company session.

**Non-Goals:**
- UI (`web/`), Core outside `api/`, contracts, engine formulas, `data/bench/`.
- Files 71–72 (bench import, employee delete/tombstone).
- Invalidating other sessions on consume.
- Admin PATCH / generate / live sandbox.

## Decisions

- **No FK on `generate_logs.restaurant_id`:** a restaurant can disappear later; the log row must remain. Backfill joins `restaurateur_accounts.email` (lowercase) to `generate_logs.email`.
- **No FK on `impersonate_tokens`:** mint already 404s if company or account is missing; leftover tokens expire.
- **Score from the generated slot:** `score_global` is `slot["score"]["global"]` of the cycle just written (sync 200 and Maximal persist), not the restaurant’s latest slot.
- **Absolute URL:** prefer `X-Forwarded-Proto` + `X-Forwarded-Host` when both exist so copied links work behind Railway’s proxy; otherwise `request.base_url`.
- **SPA parameterized routes** sit next to `/admin/bench/run/{run_id}` in `_mount_spa`, not in the static `SPA_PATHS` tuple.

## Risks / Trade-offs

- [Stale admin planning] → Freeze is live GET, not a snapshot of the generate row.
- [Forwarded host spoofing] → Only the admin mint path uses those headers; consume is public but the token is one-shot and hashed.
- [Pre-existing Saint-Cloud / engine-ref pytest failures] → Do not “fix” them; only new tests must be green.

## Migration Plan

`alembic upgrade head` adds columns and table, then backfills `restaurant_id`. Rollback drops the table and columns. Old API clients ignore the extra JSON keys.

## Open Questions

None — freeze is complete.
