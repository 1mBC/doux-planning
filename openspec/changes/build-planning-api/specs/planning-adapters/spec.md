## Purpose

Exposes the existing domain and constraint engine over HTTP so the restaurateur can persist configuration, score and edit a sandbox, and so the employee can read published own-shifts — always by calling the engine and serializing its result.

## ADDED Requirements

### Requirement: One scoring path through the engine
HTTP evaluate, swap, rank, sandbox rescore, and generate-job completion MUST call the constraint engine and serialize its result (assignments and warnings). The adapter MUST NOT recompute warning severity, empty posts, contract hours, or candidate order in HTTP code. Optional `stats` on a serialized result MUST be counts taken from that engine result and the assignments it returned, not a second scoring model. Live adapter responses are not required to include the frozen example’s `legal_rows` / `wish_rows` tables.

#### Scenario: Evaluate is engine output
- **WHEN** the restaurateur posts the current sandbox draft to evaluate
- **THEN** the response assignments and warnings are those returned by the engine for that draft

#### Scenario: Swap is dual reassignment
- **WHEN** the restaurateur posts two shifts to swap in the sandbox
- **THEN** the response is the engine result of exchanging those two people, persisted on the sandbox

#### Scenario: Rank uses the engine per candidate
- **WHEN** the restaurateur asks who can take an empty slot
- **THEN** the response lists candidates in engine rank order, each with the engine warnings for placing that person

### Requirement: Synchronous adapters except generate
Evaluate, swap, rank, sandbox enter, sandbox edit, sandbox discard, and publish SHALL complete in the request and return the outcome in that response. They MUST NOT create a generation job. Generate remains the job-backed path.

#### Scenario: Swap is immediate
- **WHEN** the restaurateur posts a swap
- **THEN** the response includes the engine result without a `job_id`

#### Scenario: Evaluate is not a job
- **WHEN** the restaurateur posts evaluate
- **THEN** no generation job row is created

### Requirement: Live sandbox HTTP wraps Core per team
The restaurateur SHALL edit a published team cycle through `/v1/live/sandbox/{team}` (Bearer company). Routes MUST wrap Core `enter_live_sandbox`, preview / apply / undo (same proposal shapes as the public joujou), `discard_live_sandbox`, and `publish_live_sandbox`. `team` is `salle` or `cuisine`. `NoPublishedCycle` MUST be HTTP 409 `Aucun cycle publié pour cette équipe.` Discard MUST re-enter the current published cycle (empty history). Publish MUST write only that team’s `published_cycles` key, close the draft (`GET` live → 404), and leave the other team intact. A non-null cycle on `POST /v1/live/sandbox/{team}/publish` MUST include the same Core `cycle_recap` keys as `POST /v1/generate` (`stats`, `legal_cols`, `legal_rows`, `wish_cols`, `wish_rows`) — serialized from `cycle_recap`, not invented in `api/`. Public `/v1/sandbox/*` MUST stay unauthenticated and unchanged. Week reconciliation, evaluate / swap / rank, and `/me/shifts` remain later slices.

#### Scenario: Enter salle after generate
- **WHEN** salle has a published cycle and the restaurateur posts enter for `salle`
- **THEN** the response is HTTP 200 `LiveState` with `"team": "salle"` and the published assignments

#### Scenario: Enter cuisine without a published cycle
- **WHEN** only salle is published and the restaurateur posts enter for `cuisine`
- **THEN** the response is HTTP 409 French and no cuisine draft is stored

#### Scenario: Discard restores published
- **WHEN** the restaurateur retunes, commits, then discards
- **THEN** a subsequent enter matches the published assignments with empty history

#### Scenario: Publish updates cycles only
- **WHEN** the restaurateur publishes a retuned salle draft
- **THEN** `GET /v1/cycles` shows the new salle cycle, `cuisine` stays `null`, and `GET /v1/live/sandbox/salle` is 404

#### Scenario: Publish includes cycle recap
- **WHEN** the restaurateur publishes a live salle sandbox
- **THEN** `published.salle` includes `stats`, `legal_cols`, `legal_rows`, `wish_cols`, and `wish_rows` from Core `cycle_recap`, and `published.cuisine` stays `null`

### Requirement: Restaurateur can persist configuration
Authenticated restaurateur routes SHALL allow reading and updating staff, structures, hours, cycle, weeks, and intents for the session restaurant. Employee sessions MUST be rejected on those writes. Updates that change coverage MUST go through the cycle sandbox as already required by cruise-planning.

#### Scenario: Restaurateur reads staff
- **WHEN** the restaurateur gets the employee list
- **THEN** the response contains that restaurant’s employees including contracts and restaurateur-owned constraints

#### Scenario: Employee cannot patch hours
- **WHEN** an employee session patches restaurant hours
- **THEN** the request is rejected and hours are unchanged

### Requirement: Employee planning route
`GET /v1/me/planning` (Bearer employee) SHALL wrap Core `employee_board` for `me.employee_id`. The 200 body MUST be `{ employee_id, team, week_labels, employees, assignments, contract, wishes, unavailabilities }` per `contracts/http/v1-me-planning.md`. `week_labels` MUST be Core `week_label_scheme`. `wishes` MUST be Core `BoardWish` objects (`kind`, `held`, optional `value` / `service_id` / `limit`) and MUST NOT use `{ key }`. A posed `weekend_rest_day` MUST appear as `{ kind: "weekend_rest_day", held }` — the adapter MUST NOT filter that kind. `unavailabilities` MUST be `{ weekday, service_id }`. `assignments` MUST be the full published team grid (empty if that team has no cycle). `employees` MUST be the fiches of that team (no `invite_token`). The route MUST NOT return live sandbox drafts, `/me/shifts`, or snapshot `legal_rows` / `wish_rows`. A company session MUST receive HTTP 403 `Action réservée au salarié.`

#### Scenario: Salle employee sees the published team grid
- **WHEN** a linked salle employee gets `/v1/me/planning` after a salle generate
- **THEN** `assignments` matches the published salle cycle (every teammate’s shifts), `employee_id` is that account, `contract` is present, and each wish has `kind` (not `key`)

### Requirement: Context exposes Core wellbeing and week labels
`GET /v1/context` (Bearer company) MUST include `week_labels` from Core `week_label_scheme` (`"ab"` or `"parity"`) and serialize each employee `wellbeing` as the Core object plus `unavailabilities` `{ weekday, service_id }`. GET / export / generate / me/planning MUST coerce stored Railway wellbeing JSONB to that Core shape before serializing and MUST NOT emit a key list or `every_*`. PATCH MUST accept that same employee shape, MUST reject `week_labels` as a written field, and MUST reject legacy wellbeing / indispo shapes with HTTP 400 `Champs invalides.` `weekend` `even` or `odd` on any fiche MUST yield `"parity"`; `every_two` alone MUST yield `"ab"`.

#### Scenario: Even weekend switches restaurant labels to parity
- **WHEN** a restaurateur patches one fiche `wellbeing.weekend` `even` then gets `/v1/context`
- **THEN** `week_labels` is `parity` and the fiche wellbeing is an object

#### Scenario: Every-two weekend keeps A/B labels
- **WHEN** the only weekend choice on staff is `every_two`
- **THEN** `GET /v1/context` returns `week_labels` `ab`

#### Scenario: Unpublished live cran is invisible
- **WHEN** the restaurateur has an uncommitted-to-publish live sandbox edit
- **THEN** `/v1/me/planning` still returns the published assignments

#### Scenario: Company cannot read employee planning
- **WHEN** a company session gets `/v1/me/planning`
- **THEN** the response is HTTP 403 French

### Requirement: Example seed HTTP wraps Core
`POST /v1/context/seed-example` (Bearer company, no body) SHALL wrap Core `seed_example_context` and return HTTP 200 with the same `Context` body as `GET /v1/context`. An employee session MUST receive HTTP 403 `Action réservée au restaurateur.` Missing Bearer MUST be 401. Without `DATABASE_URL` the route MUST be 503 `Base indisponible.` The public example MUST stay 92 assignments. The adapter MUST NOT call `hydrate_delivered_cycle`.

#### Scenario: Company seed returns the smashed context
- **WHEN** a company session posts `/v1/context/seed-example`
- **THEN** the 200 body matches a subsequent GET (ready salle, not cuisine, example fiches, `week_labels` `ab`)

#### Scenario: Employee cannot seed
- **WHEN** an employee session posts `/v1/context/seed-example`
- **THEN** the response is HTTP 403 French

### Requirement: Context export and import
`GET /v1/context/export` (Bearer company) SHALL return `{ export_version: 1, name, services, ladders, employees, types, typical_week }` generated from the live context. The body MUST NOT include `company_code` or `invite_token`. `POST /v1/context/import` SHALL accept that shape, ignore forbidden keys (`company_code`, `invite_token`, `ready`, `week_labels`, `legal_context_id`), smash like `POST /v1/context/seed-example` (clear cycles / live sandboxes / linked ids, delete this company’s employee accounts), apply the JSON `name`, mint new Core `invite_token`s, and return the same `Context` body as GET. `export_version` other than `1` MUST be HTTP 400 `Champs invalides.` Employee Bearer MUST be 403. Missing Bearer MUST be 401. Without `DATABASE_URL` MUST be 503. The public example MUST stay 92. The adapter MUST NOT call `generate_cycle`.

#### Scenario: Export strips secrets
- **WHEN** a company session gets `/v1/context/export`
- **THEN** `export_version` is `1` and the JSON has no `company_code` or `invite_token`

#### Scenario: Import smashes a linked company
- **WHEN** a company with a linked employee and a published cycle posts a valid export body
- **THEN** the response is HTTP 200, cycles are null, linked ids are empty, and the old employee Bearer is HTTP 401

#### Scenario: Unknown export version is rejected
- **WHEN** the restaurateur posts import with `export_version` `2`
- **THEN** the response is HTTP 400 `Champs invalides.`

### Requirement: Product errors are French
Protected and public API error bodies SHALL present a French `message` suitable to show in the product. OpenSpec requirements remain in English.

#### Scenario: French 401
- **WHEN** a protected route is called without a session
- **THEN** the error message is French
