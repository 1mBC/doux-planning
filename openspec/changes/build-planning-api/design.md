## Context

See `proposal.md` for why. Domain and engine already live under `src/doux_planning/` (`generate_cycle`, `evaluate`, `rank_candidates`, `swap_shifts`, `publish_allowed`, `PlanningStore`, `redeem_invite`). HTTP today is file-backed `GET /v1/examples/{id}` in `src/doux_planning/api/`. `define-planning-core` stays open and is not archived or synced. `build-planning-ui` consumes the public example route only. Do not edit the engine package outside `api/` unless a blocker is confirmed with the user.

Engine time bounds already exist (`SEARCH_SECONDS`: minimal 3s, optimized 30s, maximal 600s). The job layer exposes those numbers as `estimated_seconds`.

## Goals / Non-Goals

**Goals:**
- Postgres-backed live store plus FastAPI adapters that call the engine and serialize its result.
- Public example contract preserved (same JSON keys, no auth, no solve).
- Password sessions for company (`kind: company`) and employee; restaurant id only from the session. Unified `/v1/auth/register` and `/v1/auth/login` per `contracts/http/v1-auth.md`.
- Generate as a Postgres job + worker poll; other engine calls stay in-request.

**Non-Goals:**
- React, CORS-for-UI unless a later verify forces it, Redis/Celery, OAuth, SMTP, multi-restaurant, employee-authored constraints, rebuilding `legal_rows` / `wish_rows` on live results, changing keep-best / rest / coupure / min-shift rules.

## Decisions

### 1. Adapters only in `api/`; in-memory `PlanningStore` stays for domain tests

HTTP handlers load/save restaurant state through a Postgres-backed store that offers the same operations as `PlanningStore` (sandbox enter/edit/discard/publish, generate-into-sandbox, employee_view, reconciliations). Scoring stays in `engine.py`. Existing in-memory `PlanningStore` remains the domain unit-test double.

Alternative: rewrite `PlanningStore` itself onto SQL. Rejected — would touch `planning.py` without a blocker, and mix persistence into the module the user asked to leave alone.

### 2. Frozen example snapshot vs live restaurant

Seed writes:
- `legal_contexts` from `data/legal/france.json`
- restaurant + staff + structures + hours from `data/examples/saint-cloud.json` (`legal_context = france`)
- `example_snapshots` row `{example_id, restaurant_id, planning jsonb}` copied from the file’s `planning` object

`GET /v1/examples/{id}` reads `example_snapshots` + `legal_contexts` + restaurant public fields. It never calls `generate_cycle`. Live generate/publish update cycle/sandbox tables only, so the UI example contract cannot drift.

Alternative: public GET returns the live published cycle. Rejected — `build-planning-ui` and the frozen file are a contract; a later generate would change stats (70 assignments, etc.).

### 3. After seed, no file runtime

`DATABASE_URL` required for the API process. Seed/migrate reads `data/` once. Example and legal reads then hit Postgres. Pytest for the public route uses a test database (extend `tests/test_planning.py`), not a second file adapter in production code.

### 4. Auth: Argon2 hashes + opaque sessions in Postgres

Live companies are **not** the seeded `restaurants` / Saint-Cloud snapshot row. New tables: live company (`id`, `invite_code`, `name` `""`, `linked_employee_ids`), live fiches (`id`, `company_id`, `name`, `role`, `team`, `invite_token`), `restaurateur_accounts` / `employee_accounts` (email unique **global**, Argon2 `password_hash`), `sessions` (`token_hash`, kind `company`|`employee`, `account_id`, `restaurant_id`, `expires_at`). Login/register return the raw token once; `Authorization: Bearer`. Logout deletes the session row.

No JWT. No cookies required.

`POST /v1/auth/register`: `kind: company` → `RestaurantIdentity(...)` Core, persist invite code, one restaurateur, **new** empty company (not Saint-Cloud). `kind: employee` → load identity + fiches, wrap `redeem_invite` (QR `employee_token` or manual `employee_id`). `POST /v1/auth/login` is a single screen; `kind` comes from `me`. `GET /v1/me`. `POST /v1/auth/logout`. `GET /v1/invites/{company_code}` public (unlinked fiches only, no tokens). `POST /v1/staff/{id}/invite-token` company Bearer → `rotate_employee_invite_token`.

Do not implement `/v1/auth/restaurateur/*` or `/v1/auth/employee/*`. Without `DATABASE_URL`, auth/invites/rotate/context return 503; example dual-read and public sandbox stay unchanged. Errors use `{ "detail": "<French>" }` like the sandbox.

Live context (`contracts/http/v1-context.md`): extend `companies` / `staff_fiches`. `GET` / `PATCH /v1/context` wrap Core `empty_restaurant`, mutators, and `team_ready`. Register company already persists an empty live company; GET returns that empty shape (`ready` false) without `generate_cycle`. PATCH keys are optional section replacements. New fiches get a Core `invite_token`; rotate stays `POST /v1/staff/{id}/invite-token`. Do not write `example_snapshots` or Saint-Cloud files.

### 5. Route map (restaurant id never in the path)

Public:
- `GET /v1/examples/{example_id}`
- `GET /v1/invites/{company_code}`
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `/v1/sandbox/*` (unchanged in the auth slice)

Session:
- `POST /v1/auth/logout` (Bearer)
- `GET /v1/me` (Bearer)

Restaurateur (company Bearer), this slice:
- `GET|PATCH /v1/context`
- `POST /v1/staff/{id}/invite-token`

Restaurateur:
- `GET|PATCH /v1/restaurant` (hours, name, legal_context id)
- `GET|POST|PATCH /v1/staff`, structures, hours as needed
- `GET /v1/cycle`, `GET /v1/weeks`
- `POST /v1/sandbox/enter|discard`, `POST /v1/sandbox/edit`, `POST /v1/sandbox/publish` (acknowledged warning keys)
- `POST /v1/evaluate`, `/v1/swap`, `/v1/rank`
- `POST /v1/generate` → job metadata
- `GET /v1/jobs/{job_id}`

Employee:
- `GET /v1/me/shifts`

Errors: `{ "error": { "code": "...", "message": "<French>" } }`. Existing example 404 may keep FastAPI `detail` only if tests already assert it; prefer the structured shape for new routes and align the example route if it does not break the UI (UI only needs 200 body keys).

### 6. Generate jobs: table + SKIP LOCKED worker, not Celery

`jobs (id, restaurant_id, kind='generate', status, search_effort, estimated_seconds, elapsed_seconds, result jsonb, error_message, created_at, started_at, finished_at)`.

`POST /v1/generate` inserts `queued`, returns `job_id`, `status`, `search_effort`, `estimated_seconds` from `SEARCH_SECONDS` (imported from the engine module — time bound, not a score). Worker: `SELECT … FOR UPDATE SKIP LOCKED`, set `running`, call `generate_cycle(sandbox.draft, search)`, write sandbox, store serialized `EngineResult`, set `done` / `failed`.

Compose services: `db`, `api` (uvicorn), `worker` (same image, different command). No Redis.

evaluate / swap / rank / sandbox stay synchronous as specified.

### 7. Serialize `EngineResult` only

JSON: `assignments` (including `duration_hours` as a derived field already on `Shift`) and `warnings` (`severity`, `code`, `message`, `employee_id`, `day_index`). Optional `stats` = counts from that result (`assignments`, `empty` from `empty_post`, `interdit`, `souhait`, `below_role` from assignments vs roles). Do not generate `legal_rows` / `wish_rows` on live adapters in this change; those stay on the frozen example snapshot.

### 8. Schema and stack

PostgreSQL 16, SQLAlchemy 2 (sync) + Alembic, psycopg, Argon2. FastAPI handlers stay `def` (CPU-bound generate is in the worker). Docker Compose on the VPS as already chosen. One restaurant, ~15–25 employees — no extra cache layer.

## Risks / Trade-offs

- [API tests need Postgres] → Extend existing tests with a `DATABASE_URL`; document Compose. Do not add SQLite as a second dialect.
- [Worker down leaves jobs queued] → Status stays `queued`; UI keeps polling `estimated_seconds`. No fake result.
- [In-process generate would block uvicorn] → Dedicated worker service.
- [Restaurateur register race] → Unique email constraint (global) + one restaurateur per new live company, never bind to Saint-Cloud.
- [Invite preview leaks first names] → Acceptable: the code is the secret, human-scale staff list.
- [Temptation to “fix” the engine while wiring jobs] → Call `generate_cycle` / `evaluate` as-is; stop and ask if a result looks wrong.

## Migration Plan

Greenfield DB: `alembic upgrade` then seed. Rollback: drop Compose volumes; data files still hold the frozen example. No change to `define-planning-core` artifacts. Public example remains compatible with `build-planning-ui`.

## Open Questions

None that change specs or task order. Password minimum is 8 characters per the frozen HTTP contract.
