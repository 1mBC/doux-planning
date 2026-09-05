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

Alternative: public GET returns the live published cycle. Rejected — `build-planning-ui` and the frozen file are a contract; a later generate would change stats (92 assignments, etc.).

### 3. After seed, no file runtime

`DATABASE_URL` required for the API process. Seed/migrate reads `data/` once. Example and legal reads then hit Postgres. Pytest for the public route uses a test database (extend `tests/test_planning.py`), not a second file adapter in production code.

### 4. Auth: Argon2 hashes + opaque sessions in Postgres

Live companies are **not** the seeded `restaurants` / Saint-Cloud snapshot row. New tables: live company (`id`, `invite_code`, `name` `""`, `linked_employee_ids`), live fiches (`id`, `company_id`, `name`, `role`, `team`, `invite_token`), `restaurateur_accounts` / `employee_accounts` (email unique **global**, Argon2 `password_hash`), `sessions` (`token_hash`, kind `company`|`employee`, `account_id`, `restaurant_id`, `expires_at`). Login/register return the raw token once; `Authorization: Bearer`. Logout deletes the session row.

No JWT. No cookies required.

`POST /v1/auth/register`: `kind: company` → `RestaurantIdentity(...)` Core, persist invite code, one restaurateur, **new** empty company (not Saint-Cloud). `kind: employee` → load identity + fiches, wrap `redeem_invite` (QR `employee_token` or manual `employee_id`). `POST /v1/auth/login` is a single screen; `kind` comes from `me`. `GET /v1/me`. `POST /v1/auth/logout`. `GET /v1/invites/{company_code}` public (unlinked fiches only, no tokens). `POST /v1/staff/{id}/invite-token` company Bearer → `rotate_employee_invite_token`.

Do not implement `/v1/auth/restaurateur/*` or `/v1/auth/employee/*`. Without `DATABASE_URL`, auth/invites/rotate/context return 503; example dual-read and public sandbox stay unchanged. Errors use `{ "detail": "<French>" }` like the sandbox.

Live context (`contracts/http/v1-context.md`): extend `companies` / `staff_fiches`. `GET` / `PATCH /v1/context` wrap Core `empty_restaurant`, mutators, and `team_ready`. Register company already persists an empty live company; GET returns that empty shape (`ready` false) without `generate_cycle`. PATCH keys are optional section replacements. New fiches get a Core `invite_token`; rotate stays `POST /v1/staff/{id}/invite-token`. Do not write `example_snapshots` or Saint-Cloud files.

HTTP wellbeing wrap (Core already owns the model): persist `staff_fiches.wellbeing` as the Core object JSON. Read: object → parse; `[]` / absent → `Wellbeing()`; legacy preference keys or `every_morning` / `every_evening` → HTTP 400 `Champs invalides.` No aliases, no `WellbeingPreference`. PATCH/GET `employees[]` use `wellbeing` object + `unavailabilities: [{ weekday, service_id }]`. `GET /v1/context` and `GET /v1/me/planning` add `week_labels` from `week_label_scheme` (`"ab"` | `"parity"`). `week_labels` is read-only — PATCH must not accept it (same as `ready`). `GET /v1/me/planning` wishes are Core `BoardWish` (`kind`, `held`, optional `value` / `service_id` / `limit`), never `{ key }`. Public example stays the stored Core snapshot (92 / 17 / 10/12 / 47). Do not edit `engine.py`, `staff.py`, `hydrate.py`, or `data/examples/saint-cloud.json`.

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
- `POST /v1/generate` (sync `generate_team`)
- `GET /v1/cycles`
- `/v1/live/sandbox/{team}` enter / GET / preview / commit / undo / discard / publish

Restaurateur:
- `GET|PATCH /v1/restaurant` (hours, name, legal_context id)
- `GET|POST|PATCH /v1/staff`, structures, hours as needed
- `GET /v1/cycle`, `GET /v1/weeks`
- `POST /v1/sandbox/enter|discard`, `POST /v1/sandbox/edit`, `POST /v1/sandbox/publish` (acknowledged warning keys)
- `POST /v1/evaluate`, `/v1/swap`, `/v1/rank`
- `POST /v1/generate` (sync; this slice)
- `GET /v1/cycles` (this slice)
- `GET /v1/jobs/{job_id}` (later; not in this slice)

Employee:
- `GET /v1/me/planning` (this slice; wrap `employee_board`)

Errors: `{ "error": { "code": "...", "message": "<French>" } }`. Existing example 404 may keep FastAPI `detail` only if tests already assert it; prefer the structured shape for new routes and align the example route if it does not break the UI (UI only needs 200 body keys).

### 6. Generate is sync `generate_team` (no jobs in this slice)

`POST /v1/generate` `{ team, search_effort? }` (Bearer company) loads the live context, wraps Core `generate_team`, persists `published_cycles` JSONB on the company (`salle` / `cuisine` independently), and returns 200 `{ team, search_effort, published }`. Omitted effort is `optimized`. `TeamNotReady` → 409 `Cette équipe n'est pas prête à calculer.` with no solver call. `GET /v1/cycles` returns the persisted `{ published }` (both null until generated). Tests use `minimal` only.

Do **not** add a `jobs` table, Compose worker, or `SKIP LOCKED` in this slice. The old async-job design is deferred. Do not write `example_snapshots` or Saint-Cloud files.

evaluate / swap / rank stay later. Live sandbox HTTP is this slice (`/v1/live/sandbox/{team}`).

### 7. Serialize `EngineResult` only

JSON: `assignments` (including `duration_hours` as a derived field already on `Shift`) and `warnings` (`severity`, `code`, `message`, `employee_id`, `day_index`). Optional `stats` = counts from that result (`assignments`, `empty` from `empty_post`, `interdit`, `souhait`, `below_role` from assignments vs roles). Do not generate `legal_rows` / `wish_rows` on live adapters in this change; those stay on the frozen example snapshot.

### 8. Schema and stack

PostgreSQL 16, SQLAlchemy 2 (sync) + Alembic, psycopg, Argon2. FastAPI handlers stay `def` (CPU-bound generate is in the worker). Docker Compose on the VPS as already chosen. One restaurant, ~15–25 employees — no extra cache layer.

### 9. Live sandbox HTTP wraps Core per team

`/v1/live/sandbox/{team}` (Bearer company) wraps `enter_live_sandbox`, `PlanningStore` preview / apply / undo with `team=`, `discard_live_sandbox`, and `publish_live_sandbox`. Persist brouillons on `companies.live_sandboxes` JSONB — not `sandbox_sessions`, not `example_snapshots`. `NoPublishedCycle` → 409 `Aucun cycle publié pour cette équipe.` Preview shapes match the joujou (`v1-sandbox-edit.md`) plus `"team"`. Public `/v1/sandbox/*` stays unchanged and unauthenticated. Tests use generate `minimal` only.

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
