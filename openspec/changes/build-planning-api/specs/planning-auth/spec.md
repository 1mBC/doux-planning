## Purpose

Authenticates company (restaurateur) and employee accounts with email and password on the unified HTTP contract, scopes later restaurant routes to the session’s restaurant, and keeps the public example plus sandbox routes unauthenticated in this slice.

## ADDED Requirements

### Requirement: Unified register and login
The system SHALL expose `POST /v1/auth/register` and `POST /v1/auth/login` only (no `/v1/auth/restaurateur/*` or `/v1/auth/employee/*`). Register MUST accept `{ kind, email, password, company_code?, employee_token?, employee_id? }` and return HTTP 201 `{ token, me }`. Login MUST accept `{ email, password }` and return HTTP 200 `{ token, me }`. `me.kind` MUST be `"company"` or `"employee"` (never `"restaurateur"`). For `kind: company`, `me.employee_id` MUST be `null`. Passwords MUST be at least 8 characters and stored with Argon2. Email MUST be unique across company and employee accounts. The system MUST NOT offer OAuth or a magic-link / email-token sign-in.

#### Scenario: Company register creates a new empty restaurant
- **WHEN** a caller registers with `kind` `company`, email, and password and does not send employee fields
- **THEN** a new live company is created with name `""` and a Core `RestaurantIdentity` invite code, one restaurateur account is created for that company, a session is issued, and the account is not attached to the Saint-Cloud example restaurant

#### Scenario: Company register rejects employee fields
- **WHEN** a company register includes `company_code`, `employee_token`, or `employee_id`
- **THEN** the request is rejected with HTTP 400 and French `detail` `Champs invalides.`

#### Scenario: Duplicate email rejected
- **WHEN** a caller registers with an email that already exists on any account
- **THEN** the request is rejected with HTTP 409 and French `detail` `Cet email est déjà utilisé.`

#### Scenario: Unified password login
- **WHEN** a caller posts email and password that match a company or employee account
- **THEN** a session is issued and `me.kind` reflects that account

#### Scenario: Wrong password
- **WHEN** a caller submits a wrong password (or unknown email)
- **THEN** the request is rejected with HTTP 401, French `detail` `Email ou mot de passe incorrect.`, and no session is issued

### Requirement: Employee register wraps Core invite redeem
The system SHALL let an employee register with `kind` `employee`, required `company_code`, and either QR `employee_token` or manual `employee_id`, by calling Core `redeem_invite`. A valid redeem MUST persist the employee account, update `linked_employee_ids`, and issue a session. Invalid company code or unknown token MUST map to HTTP 400 `Code entreprise ou jeton invalide.` An already-linked fiche MUST map to HTTP 409 `Cette fiche a déjà un compte.` The system MUST NOT let an employee write unavailabilities, wellbeing preferences, or other staff constraints.

#### Scenario: Employee joins with manual fiche
- **WHEN** an employee registers with a valid `company_code`, an unlinked `employee_id`, email, and password
- **THEN** Core `redeem_invite` links that fiche and a session is issued with `me.kind` `employee` and that `employee_id`

#### Scenario: Employee joins with QR token
- **WHEN** an employee registers with a valid `company_code` and `employee_token` for an unlinked fiche
- **THEN** that fiche is linked and a session is issued

#### Scenario: Invalid company code
- **WHEN** an employee presents a `company_code` that does not match a live company
- **THEN** registration is rejected with HTTP 400 and no account is created

#### Scenario: Already linked fiche
- **WHEN** an employee tries to register against a fiche already in `linked_employee_ids`
- **THEN** registration is rejected with HTTP 409

### Requirement: Public invite preview lists unlinked fiches only
`GET /v1/invites/{company_code}` SHALL be public. A valid code MUST return `{ restaurant_name, employees }` where `employees` are fiches not in `linked_employee_ids`, each with `id`, `name`, `role` (job name string), and `team` (`"salle"` | `"cuisine"`). The response MUST NOT include `invite_token`, email, or password hashes. An unknown code MUST return HTTP 404 `Entreprise introuvable.`

#### Scenario: Preview with valid code
- **WHEN** a caller presents a valid company invite code before registering
- **THEN** the system returns the restaurant name and the unlinked employee profiles and does not require a session

#### Scenario: Linked fiches are omitted
- **WHEN** a fiche has been redeemed
- **THEN** a subsequent invite preview does not include that fiche

### Requirement: Company can rotate an employee invite token
`POST /v1/staff/{id}/invite-token` SHALL require a company Bearer session and MUST call Core `rotate_employee_invite_token`, persist the new token, and return HTTP 200 `{ employee_id, employee_token }` once. An employee session MUST be HTTP 403 `Action réservée au restaurateur.` A fiche unknown or belonging to another company MUST be HTTP 404 `Fiche introuvable.`

#### Scenario: Rotate returns a fresh token
- **WHEN** a company session rotates the invite token of a fiche it owns
- **THEN** the previous token no longer redeems and the response contains the new token

### Requirement: Opaque hashed sessions
Sessions SHALL use `Authorization: Bearer <token>`. The raw token MUST be returned once at register/login and MUST NOT be persisted; only a hash is stored. `GET /v1/me` MUST return `me` for a valid session. `POST /v1/auth/logout` MUST return HTTP 204 and invalidate that token. Missing, unknown, expired, or already-logged-out tokens on protected auth routes MUST return HTTP 401 `Session invalide.` Authenticated restaurant routes SHALL use `restaurant_id` from the session, not from the path.

#### Scenario: Me after login
- **WHEN** a client calls `GET /v1/me` with a valid Bearer token
- **THEN** the response is the `me` object without `token`

#### Scenario: Logout kills the token
- **WHEN** a client logs out then calls `GET /v1/me` with the same token
- **THEN** the request is rejected with HTTP 401

#### Scenario: Unauthenticated protected route
- **WHEN** a client calls `GET /v1/me` or logout without a valid session
- **THEN** the request is rejected and no restaurant account data is returned

### Requirement: Auth requires the live database; public example and sandbox do not
When `DATABASE_URL` is unset, auth, invites, and invite-token routes MUST return HTTP 503 `Base indisponible.` `GET /v1/examples/saint-cloud` MUST keep its dual-read file fallback. `/v1/sandbox/*` MUST remain public without Bearer in this slice.

#### Scenario: Auth without database
- **WHEN** a client posts register or login while `DATABASE_URL` is unset
- **THEN** the response is HTTP 503 and no account is created

#### Scenario: Example stays public with or without a session
- **WHEN** a client gets `/v1/examples/saint-cloud` with or without a Bearer token
- **THEN** the response is HTTP 200 with the frozen example (including 92 assignments)

#### Scenario: Sandbox stays public
- **WHEN** a client calls existing sandbox routes without Authorization
- **THEN** those routes still succeed as in the sandbox slice

### Requirement: Restaurateur may configure, generate, sandbox, and publish
A restaurateur (company) session SHALL be authorized to read and write restaurant configuration, enter the sandbox, request generation, evaluate, swap, rank, and publish once those routes are locked. An employee session MUST be rejected on those mutating or sandbox routes when they become session-scoped. This slice MUST NOT lock `/v1/sandbox/*`.

#### Scenario: Restaurateur generate allowed
- **WHEN** a restaurateur with a valid session requests generation (later slice)
- **THEN** the request is authorized for that restaurant

#### Scenario: Employee cannot sandbox once locked
- **WHEN** an employee session calls sandbox enter, edit, discard, publish, or generate after those routes require auth
- **THEN** the request is rejected with a French error and the sandbox is unchanged

### Requirement: Employee reads only own published shifts
An employee session SHALL receive only that employee’s shifts from the last published cycle or week instances. The system MUST NOT include other employees’ assignments, MUST NOT include sandbox drafts, and MUST NOT expose the full team grid.

#### Scenario: Own published shifts
- **WHEN** an employee with a linked account requests their planning
- **THEN** the response contains only that employee’s published shifts

#### Scenario: Sandbox is hidden
- **WHEN** the restaurateur has unpublished sandbox edits
- **THEN** the employee planning response still matches the last published assignments for that employee

### Requirement: Admin promote and generate log read
`me` SHALL include `admin` (bool). Company `admin` MUST be the restaurateur `is_admin` flag. Employee `admin` MUST be false. `kind` MUST stay `"company"` or `"employee"` (never `"admin"`). At boot, `ADMIN_EMAIL` MUST promote an existing restaurateur with that lowercase email and MUST NOT insert a row when the email is missing or the env is empty. `GET /v1/admin/generates` SHALL require `admin` true and return `{ entries }` newest-first. Each entry MUST include `id`, `created_at`, `email`, `restaurant_name`, `team`, `search_effort`, `duration_seconds`, and `facts` (evaluate misses plus `employee_name`). GET MUST NOT emit `warnings`. Old rows MUST emit `search_effort` and `duration_seconds` as `null`. A stored log item with `message` and no `payload` MUST hydrate to a fact (`kind` = `code`, `polarity` `miss`, `payload` `{}`) and MAY keep `message` on that item only. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.`

#### Scenario: Promote is idempotent
- **WHEN** `ADMIN_EMAIL` matches an existing restaurateur and promote runs twice
- **THEN** that account is the only row for the email and `me.admin` is true

#### Scenario: Unknown admin email creates nothing
- **WHEN** `ADMIN_EMAIL` does not match a restaurateur
- **THEN** no account is inserted

#### Scenario: Non-admin cannot list generates
- **WHEN** a company session with `admin` false gets `/v1/admin/generates`
- **THEN** the response is HTTP 403 French

### Requirement: Admin bench runs and jobs
Admin bench routes SHALL require `admin` true (`contracts/domain/bench.md`). `POST /v1/admin/bench/run` with `scope` `dataset` and `search_effort` `minimal` or `optimized` MUST be HTTP 200 `{ runs }` and MUST insert one `bench_runs` row (`app_version` = trimmed `data/bench/VERSION`). `all`, `category`, or `maximal` MUST be HTTP 202 `{ job_ids, status: queued }` with one `bench_jobs` row per dataset and MUST NOT call `run_bench` in the request. The worker SHALL claim `bench_jobs` independently of `generate_jobs` (no HTTP 409 cross-lock). A `done` job MUST insert one `bench_runs` row. Bench MUST NOT write `published_cycles` or `generate_logs`. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.`

#### Scenario: Dataset minimal persists a run
- **WHEN** an admin posts bench run `scope` `dataset` `search_effort` `minimal` for a known jeu
- **THEN** the response is HTTP 200 with one `RunSummary` and GET runs includes that row

#### Scenario: All maximal enqueues one job per jeu
- **WHEN** an admin posts bench run `scope` `all` `search_effort` `maximal`
- **THEN** the response is HTTP 202 with fifty `job_ids` and worker ticks (stubbed `run_bench`) insert fifty `bench_runs`

#### Scenario: Category crafted enqueues twenty-six jobs
- **WHEN** an admin posts bench run `scope` `category` `category` `crafted`
- **THEN** the response is HTTP 202 with twenty-six `job_ids`

#### Scenario: GET datasets lists fifty jeux
- **WHEN** an admin gets `/v1/admin/bench/datasets`
- **THEN** the response is HTTP 200 with fifty datasets and `engine_ref` `"core-2"`

#### Scenario: Duplicate Maximal enqueue is idempotent
- **WHEN** an admin posts the same dataset Maximal twice while the first job is still `queued`
- **THEN** both responses share one `job_id`

#### Scenario: Non-admin cannot run bench
- **WHEN** a company session with `admin` false posts `/v1/admin/bench/run`
- **THEN** the response is HTTP 403 French

### Requirement: Admin bench compare slices and export pack
GET `/v1/admin/bench/compare/{category}/{dataset_id}/{search_effort}` MUST return the last-run summary plus `employees` and `model` / `manual` `CycleSlice` (`assignments`, `facts`, `score`, `stats`, `legal_cols`, `legal_rows`, `wish_cols`, `wish_rows`) recomputed via Core `cycle_recap_from_draft` from persisted assignments, `expected.json`, and catalogue context. GET MUST NOT emit top-level `facts`, `assignments`, `expected`, or `warnings`. GET `/v1/admin/bench/export` with `scope` `dataset` (plus `category` and `dataset_id`) or `below_manuel` MUST return `{ export_version: 1, kind: "bench-pack", app_version, exported_at, scope, datasets }`. Catalogue `context` MUST omit `invite_token`. A jeu enters `below_manuel` when at least one last-run effort has `score.global < expected_score.global` (both non-null); the pack MUST include every run effort of those jeux. Unknown jeu or `scope=dataset` with no run MUST be HTTP 404 French. Empty `below_manuel` MUST be HTTP 200 with `datasets: []`. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.`

#### Scenario: Compare after halles minimal has recap hits
- **WHEN** an admin gets compare `tight` / `halles` / `minimal` after a dataset run
- **THEN** the response is HTTP 200 with `employees`, `model.facts` hits, and `manual.facts` hits, and MUST NOT include top-level `facts`

#### Scenario: Export dataset pack
- **WHEN** an admin gets `/v1/admin/bench/export` `scope` `dataset` for `tight` / `halles` after a run
- **THEN** the response is HTTP 200 `kind` `bench-pack` with one dataset, `manual`, and that effort

#### Scenario: Export below_manuel
- **WHEN** an admin gets `/v1/admin/bench/export` `scope` `below_manuel`
- **THEN** the response is HTTP 200 with `datasets` as a list (empty when no last-run is below Manuel)

#### Scenario: Non-admin cannot export bench pack
- **WHEN** a company session with `admin` false gets `/v1/admin/bench/export`
- **THEN** the response is HTTP 403 French

### Requirement: Admin bench engine_ref versions and run compare
HTTP bench summaries, GET datasets, GET runs, and export MUST emit `engine_ref` and `app_version` as the same string (`outcome.engine_ref` on persist; current `engine_ref()` on datasets / pack root). A stored `app_version` `"0.27.0"` MUST read as `"core-0"`. Last-run MUST be the newest row per `(category, dataset_id, search_effort, engine_ref)` so a `core-1` run MUST NOT replace a `core-0` last-run. GET compare by path MUST return the last-run of the current VERSION and HTTP 404 when that current last-run is missing. GET `/v1/admin/bench/runs/{run_id}` MUST return the same 200 shape as compare (`employees`, `model`, `manual`) and MUST NOT emit top-level `assignments` or `facts`. GET `/v1/admin/bench/versions` MUST return `{ engine_ref, engine_refs, datasets }` with merged refs (first appearance), three effort keys always present (`null` if no run), and `manual.global` from the first known run. Export dataset / `below_manuel` MUST use current last-runs only and include `engine_ref` plus `run_id` on the pack and each effort. SPA `/admin/bench/versions` and `/admin/bench/run/{run_id}` MUST serve `index.html`. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.`

#### Scenario: Halles minimal summaries use current engine_ref
- **WHEN** an admin runs halles `minimal` on the current engine
- **THEN** summaries, datasets, and export have `engine_ref` equal to `app_version` equal to `"core-2"`

#### Scenario: GET run is compare shape
- **WHEN** an admin gets `/v1/admin/bench/runs/{id}` after that halles run
- **THEN** the response is HTTP 200 with `model` and `manual` facts hits and no top-level `assignments` / `facts`

#### Scenario: Other engine_ref does not steal current compare
- **WHEN** a second row is inserted for the same jeu/effort with `app_version` `"core-1"`
- **THEN** GET versions lists both refs and GET compare path still returns the current `core-2` run

#### Scenario: Legacy 0.27.0 reads as core-0
- **WHEN** a stored run has `app_version` `"0.27.0"`
- **THEN** GET that run emits `engine_ref` and `app_version` `"core-0"`

#### Scenario: Non-admin cannot read versions
- **WHEN** a company session with `admin` false gets `/v1/admin/bench/versions`
- **THEN** the response is HTTP 403 French

### Requirement: Safe parallel workers
Workers SHALL claim one job per process via `SKIP LOCKED`, beat `heartbeat_at` every 10 s on generate and bench, and reclaim only `running` rows whose heartbeat is NULL or older than 180 s. Start MUST NOT requeue every `running` job. `bench_jobs` MUST have a partial unique key on `(category, dataset_id, search_effort)` for `queued`/`running`. Generate 409 when a Maximal is already queued/running for the same company+team MUST stay unchanged.

#### Scenario: Concurrent ticks claim distinct jobs
- **WHEN** two worker ticks run at once against two `queued` bench jobs
- **THEN** they claim two distinct job ids

#### Scenario: Fresh heartbeat is not reclaimed
- **WHEN** a `running` job has a fresh `heartbeat_at`
- **THEN** reclaim returns 0

#### Scenario: Stale heartbeat is requeued
- **WHEN** a `running` job has `heartbeat_at` older than 180 s
- **THEN** reclaim returns 1 and status is `queued`
