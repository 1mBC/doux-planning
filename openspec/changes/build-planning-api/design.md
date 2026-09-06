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
- React, CORS-for-UI unless a later verify forces it, Redis/Celery, OAuth, SMTP, multi-restaurant, employee-authored constraints, inventing recap stats/cells in `api/` (wrap Core `cycle_recap` only), changing keep-best / rest / coupure / min-shift rules.

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

HTTP wellbeing wrap (Core already owns the model): persist `staff_fiches.wellbeing` as the Core object JSON. PATCH / import stay strict: legacy preference keys, key lists, `every_morning` / `every_evening`, or fiche-level `max_*_per_week` → HTTP 400 `Champs invalides.` No aliases, no `WellbeingPreference`. GET / export / generate / me/planning **coerce-on-read** per `contracts/domain/coerce-railway.md` (list keys, removed keys, `every_*`, `service_id` null, fiche `max_*_per_week`) then heal the JSONB if it differs from `wellbeing_to_json` / new indispos. `[]` / absent → `Wellbeing()`. Already-Core object unchanged (`weekend_rest_day` absent → `false`). GET never emits the old JSON. PATCH/GET `employees[]` use `wellbeing` object + `unavailabilities: [{ weekday, service_id }]`. `GET /v1/context` and `GET /v1/me/planning` add `week_labels` from `week_label_scheme` (`"ab"` | `"parity"`). `week_labels` is read-only — PATCH must not accept it (same as `ready`). `GET /v1/me/planning` wishes are Core `BoardWish` (`kind`, `held`, optional `value` / `service_id` / `limit`), never `{ key }`. Public example stays the stored Core snapshot (92 / 17 / 10/12 / 47). Do not edit `engine.py`, `staff.py`, `hydrate.py`, or `data/examples/saint-cloud.json`.

`weekend_rest_day` is part of that same JSONB object (no Alembic). Parse missing key as Core default `false`; GET always emits the bool. Stored Railway list key `at_least_one_weekend_rest_day` maps to `weekend_rest_day: true` on **read/heal only**; PATCH / import of that key stay 400. `GET /v1/me/planning` must pass through Core `BoardWish` `kind: "weekend_rest_day"` when the box is posed (no kind filter).

HTTP example seed: `POST /v1/context/seed-example` loads the live company, wraps Core `seed_example_context` (file `restaurant` section only — never `hydrate_delivered_cycle` / `generate_cycle`), persists services, `hours` JSONB, ladders, types, typical week, and example fiches with Core `invite_token`s, then returns the same `Context` body as GET. Smash includes already-linked fiches (no 409). Clear `published_cycles`, `live_sandboxes`, and `linked_employee_ids`. Delete employee accounts and their sessions for **this** company (so an old employee Bearer is 401). Keep `companies.id`, `name`, `invite_code`, `legal_context_id`. Employee Bearer → 403. Without `DATABASE_URL` → 503. Public example stays 92.

Config export/import (`contracts/domain/export-config.md`): `GET /v1/context/export` serializes the live context now as `{ export_version: 1, name, services, ladders, employees, types, typical_week }` with `invite_token` stripped from every fiche and no `company_code`. `POST /v1/context/import` accepts that shape, ignores forbidden keys (`company_code`, `invite_token`, `ready`, `week_labels`, `legal_context_id`), and smashes like seed (reuse `_persist_state(..., smash_live=True)`). Apply name/services/ladders/employees/types/typical_week via the same Core mutators as PATCH; hours stay derived. Mint new Core tokens (do not reuse JSON tokens). `export_version` other than integer `1` → 400 `Champs invalides.` No Alembic, no `generate_cycle`.

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
- `POST /v1/context/seed-example` (wrap `seed_example_context`; smash live context; no body)
- `GET /v1/context/export` / `POST /v1/context/import` (portable config JSON `export_version: 1`; import smash like seed)
- `POST /v1/staff/{id}/invite-token`
- `POST /v1/generate` (sync `generate_team`)
- `GET /v1/cycles`
- `/v1/live/sandbox/{team}` enter / GET / preview / commit / undo / discard / publish
- `GET /v1/admin/generates` (Bearer, `me.admin` true)

Boot after seed: if `ADMIN_EMAIL` matches an existing restaurateur (lowercase), set `is_admin`. Skip when unset/empty or when no restaurateur row exists — never insert an account. `me` always includes `admin` (company from `is_admin`, employee always false). `kind` stays company|employee. Log generate only on HTTP 200 (`email`, `restaurant_name`, `team`, `warnings` of the team just solved). Alembic adds `restaurateur_accounts.is_admin` and `generate_logs`.

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

### 6. Generate is hybrid C (`contracts/domain/generate-jobs.md`)

`POST /v1/generate` `{ team, search_effort? }` (Bearer company). Omitted effort is `optimized`. `minimal` / `optimized` stay in-request: wrap Core `generate_team`, persist `published_cycles`, return 200 `{ team, search_effort, published }` and one `generate_logs` row. `maximal` MUST NOT call `generate_team` in uvicorn: insert `generate_jobs` (`queued`) and return 202 `{ job_id, team, search_effort: maximal, status: queued, estimated_seconds: 600 }` (no `published`). `TeamNotReady` → 409 `Cette équipe n'est pas prête à calculer.` with no job and no solver. A second `maximal` for the same company+team while `queued`/`running` → 409 `Un calcul maximal est déjà en cours.` The other team stays free.

`GET /v1/generate/jobs/{job_id}` (Bearer company, same restaurant): `{ job_id, team, search_effort, status, estimated_seconds }`; `published` only when `done`; `error` only when `failed`. Other company / unknown id → 404. Employee → 403. No session → 401. No `DATABASE_URL` → 503.

Worker process (`python -m doux_planning.api.worker`, Compose `worker`, Railway 2nd service, same image / `DATABASE_URL`): `SELECT … FOR UPDATE SKIP LOCKED` one `queued` → `running` → `generate_team(…, maximal)` → persist cycles like the 200 → `done` + `generate_logs`. Exception → `failed` + French `error`. Pytest calls one exported tick with `generate_team` stubbed (0 s). Do not wait 600 s. Alembic table `generate_jobs`. Do not write `example_snapshots` or Saint-Cloud files.

evaluate / swap / rank stay later. Live sandbox HTTP is this slice (`/v1/live/sandbox/{team}`).

### 7. Serialize `EngineResult` only

JSON: `assignments` (including `duration_hours` as a derived field already on `Shift`) and `warnings` (`severity`, `code`, `message`, `employee_id`, `day_index`). A non-null published cycle also carries Core `cycle_recap` (`stats`, `legal_cols`, `legal_rows`, `wish_cols`, `wish_rows`). HTTP MUST serialize that object — it MUST NOT invent counts or cells. `null` cycles have no recap keys. A stored cycle missing recap keys is hydrated then passed to `cycle_recap` on GET (no 500). Persist the recap inside existing `published_cycles` JSONB (no Alembic). Public example snapshot and joujou `/v1/sandbox/*` stay unchanged. `POST /v1/live/sandbox/{team}/publish` returns the same `published` shape.

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
