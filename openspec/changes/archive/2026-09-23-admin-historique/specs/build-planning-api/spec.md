# Spec Delta

## ADDED Requirements

### Requirement: Generate logs carry restaurant_id and score_global
A successful `POST /v1/generate` (HTTP 200) and a Maximal job `done` persist SHALL write `generate_logs.restaurant_id` (the company id of the solve) and `generate_logs.score_global` equal to `score.global` of the slot just generated, or `null` when that score is missing. `GET /v1/admin/generates` (Bearer admin) MUST include `restaurant_id` (`string | null`) and `score_global` (`float | null`) on every entry. Pre-existing rows without those columns MUST emit `null` for both. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.` Missing session MUST be HTTP 401. Without `DATABASE_URL` MUST be HTTP 503.

#### Scenario: Generate 200 writes both fields
- **WHEN** a company session generates a salle cycle with `search_effort` `minimal` and the slot has `score.global`
- **THEN** the matching generate log row stores that restaurant id and that global score, and GET admin generates emits both keys

#### Scenario: Legacy row emits nulls
- **WHEN** an admin lists generates and a stored row has no restaurant_id and no score_global
- **THEN** that entry includes `restaurant_id: null` and `score_global: null`

### Requirement: Admin can read a restaurant's current cycles and context
`GET /v1/admin/restaurants/{restaurant_id}/cycles` and `GET /v1/admin/restaurants/{restaurant_id}/context` SHALL require a Bearer admin session and MUST return the same JSON as `GET /v1/cycles` and `GET /v1/context` for that company (live published cycles and live context, including `invite_token` on fiches). An unknown or missing company MUST be HTTP 404 `Restaurant introuvable.` A non-admin session MUST be HTTP 403 `Action réservée à l’admin.` Missing session MUST be HTTP 401. Without `DATABASE_URL` MUST be HTTP 503. The routes MUST NOT generate, patch, or open a live sandbox.

#### Scenario: Admin cycles match company cycles
- **WHEN** an admin gets `/v1/admin/restaurants/{id}/cycles` for a restaurant that has a published salle cycle
- **THEN** the 200 body equals that restaurant’s company `GET /v1/cycles`

#### Scenario: Unknown restaurant is 404
- **WHEN** an admin gets cycles or context for a restaurant id that does not exist
- **THEN** the response is HTTP 404 `Restaurant introuvable.`

#### Scenario: Non-admin cannot view another restaurant
- **WHEN** a company session with `admin` false gets admin cycles or context
- **THEN** the response is HTTP 403 `Action réservée à l’admin.`

### Requirement: Admin can mint a one-shot impersonate link
`POST /v1/admin/impersonate` SHALL require a Bearer admin session and body `{ "restaurant_id": "<id>" }`. Success MUST be HTTP 200 `{ "url", "expires_at" }` where `url` is absolute, uses `X-Forwarded-Proto` + `X-Forwarded-Host` when both are present otherwise `request.base_url`, and has path `/impersonate/{opaque}`. The opaque token MUST be hashed (sha256) before persist. TTL MUST be 15 minutes. Missing or non-string `restaurant_id` MUST be HTTP 400 `Champs invalides.` A missing company or restaurateur account MUST be HTTP 404 `Restaurant introuvable.` Non-admin MUST be HTTP 403 `Action réservée à l’admin.` Missing session MUST be HTTP 401. Without `DATABASE_URL` MUST be HTTP 503.

#### Scenario: Mint returns an impersonate URL
- **WHEN** an admin posts impersonate for an existing restaurant with a restaurateur account
- **THEN** the response is 200 with `url` containing `/impersonate/` and an ISO UTC `expires_at`

#### Scenario: Mint missing restaurant is 404
- **WHEN** an admin posts impersonate for an unknown restaurant_id
- **THEN** the response is HTTP 404 `Restaurant introuvable.`

### Requirement: Public consume exchanges the link for a company session once
`POST /v1/auth/impersonate` SHALL be public (no Bearer) and accept `{ "token": "<opaque>" }`. Success MUST be HTTP 200 `{ "token", "me" }` like login: `me.kind` `company`, `employee_id` `null`, `me.admin` equal to `is_admin` of the target restaurateur account, session TTL 30 days, hashed opaque session. The impersonate token MUST be marked consumed. A second consume, an unknown token, or an expired token MUST be HTTP 401 `Lien expiré ou déjà utilisé.` Other sessions (including the originating admin session) MUST remain valid. Missing or non-string `token` MUST be HTTP 400 `Champs invalides.` Without `DATABASE_URL` MUST be HTTP 503.

#### Scenario: Consume then second call is 401
- **WHEN** a client posts the minted opaque token then posts it again
- **THEN** the first response is 200 company session for that restaurant and the second is HTTP 401 `Lien expiré ou déjà utilisé.`

#### Scenario: Admin session stays valid after consume
- **WHEN** an admin mints a link and another client consumes it
- **THEN** the original admin Bearer still authenticates `GET /v1/me` as admin

### Requirement: SPA serves impersonate and admin planning
When `web/dist/index.html` is present, FastAPI MUST serve that file for `GET /impersonate/{token}` and `GET /admin/planning/{restaurant_id}` the same way as `/admin/bench/run/{run_id}`.

#### Scenario: Impersonate and admin planning serve index
- **WHEN** `web/dist` exists and a client GETs `/impersonate/example-token` or `/admin/planning/example-id`
- **THEN** the response is HTTP 200 `index.html`
