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
`me` SHALL include `admin` (bool). Company `admin` MUST be the restaurateur `is_admin` flag. Employee `admin` MUST be false. `kind` MUST stay `"company"` or `"employee"` (never `"admin"`). At boot, `ADMIN_EMAIL` MUST promote an existing restaurateur with that lowercase email and MUST NOT insert a row when the email is missing or the env is empty. `GET /v1/admin/generates` SHALL require `admin` true and return `{ entries }` newest-first. Each entry MUST include `id`, `created_at`, `email`, `restaurant_name`, `team`, `search_effort`, `duration_seconds`, and `warnings` (HTTP warning plus `employee_name`). Old rows MUST emit `search_effort` and `duration_seconds` as `null`. A company or employee session with `admin` false MUST receive HTTP 403 `Action réservée à l’admin.`

#### Scenario: Promote is idempotent
- **WHEN** `ADMIN_EMAIL` matches an existing restaurateur and promote runs twice
- **THEN** that account is the only row for the email and `me.admin` is true

#### Scenario: Unknown admin email creates nothing
- **WHEN** `ADMIN_EMAIL` does not match a restaurateur
- **THEN** no account is inserted

#### Scenario: Non-admin cannot list generates
- **WHEN** a company session with `admin` false gets `/v1/admin/generates`
- **THEN** the response is HTTP 403 French
