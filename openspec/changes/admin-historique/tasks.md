# Tasks

## 1. Persist

- [x] 1.1 Alembic after `20260921_0016`: nullable `generate_logs.restaurant_id` (String, no FK) and `generate_logs.score_global` (Float); backfill `restaurant_id` from `restaurateur_accounts.email` lowercase match; create `impersonate_tokens` (`token_hash` PK, `account_id`, `restaurant_id`, `expires_at`, `consumed_at` nullable, `created_at`); update SQLAlchemy models. Verify `alembic upgrade head` on empty-or-existing Postgres
- [x] 1.2 `_log_generate` writes `restaurant_id` and `score_global` from the generated slot (`null` if missing) on sync 200 and Maximal persist. Verify generate 200 stores both columns

## 2. HTTP

- [x] 2.1 `GET /v1/admin/generates` always includes `restaurant_id` and `score_global`. Verify GET emits the keys; simulated old row is null/null
- [x] 2.2 `GET /v1/admin/restaurants/{restaurant_id}/cycles` and `/context` Bearer admin return the same JSON as company GET cycles/context. Verify admin cycles published matches company cycles; unknown id 404 `Restaurant introuvable.`; non-admin 403; no Bearer 401
- [x] 2.3 `POST /v1/admin/impersonate` mints a 15 min hashed token and absolute `/impersonate/{opaque}` URL (forwarded proto/host when both present). Verify 200 `{url, expires_at}`; invalid body 400; missing company/account 404
- [x] 2.4 `POST /v1/auth/impersonate` public consume issues a company session like login (`me.admin` = target `is_admin`), sets `consumed_at`, does not drop other sessions. Verify first 200; second 401 `Lien expiré ou déjà utilisé.`; original admin Bearer still 200 `/v1/me`
- [x] 2.5 SPA `_mount_spa` serves `/impersonate/{token}` and `/admin/planning/{restaurant_id}` as `index.html` (same pattern as `/admin/bench/run/{run_id}`). Verify TestClient 200 index when `web/dist` exists, skip otherwise

## 3. Tests

- [ ] 3.1 TestClient coverage (`skipif` without `DATABASE_URL`) for generate fields, GET keys, admin vs company cycles, impersonate mint/consume/401, admin session intact, 403/404. Do not fix pre-existing Saint-Cloud / engine-ref failures. Verify new tests green
