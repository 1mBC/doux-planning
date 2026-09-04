## Purpose

Lets the restaurateur open a French web screen that shows the engine’s Saint-Cloud example snapshot: 14-day paper grid, warnings, stats, legal rows, and wish rows — plus login / register / session — without scoring, generating, or deciding in the client.

## ADDED Requirements

### Requirement: Client loads only the example snapshot
The web client SHALL obtain restaurant, legal context, and planning data solely by calling `GET /v1/examples/saint-cloud`. It MUST NOT embed a second copy of the snapshot as source of truth, and MUST NOT invoke the constraint engine. Auth routes (`/v1/auth/*`, `/v1/me`, `/v1/invites/{company_code}`) and `GET`/`PATCH /v1/context` MAY be called for session / company context and MUST NOT feed the example grid. The client MUST NOT send `Authorization` on `/v1/examples/*` or `/v1/sandbox/*`.

#### Scenario: Successful load
- **WHEN** the restaurateur opens the example screen and the example route returns 200 with `example`, `legal`, `restaurant`, and `planning`
- **THEN** the screen is built from that JSON and no other planning request is made

#### Scenario: API unavailable
- **WHEN** the example route fails or the payload is missing required keys
- **THEN** the client shows a French error state and does not invent a planning

### Requirement: Fourteen-day paper grid from assignments
The client SHALL render a 14-day cruise grid as two week sheets (days 0–6 week A, days 7–13 week B). Rows SHALL be grouped by role then person, with two service rows (midi / soir). Each day SHALL show start, end, and duration for the assignment on that person/service/day when one exists in `planning.assignments`; an empty cell SHALL mean rest. The client MUST place shifts using `day_index`, `employee_id`, and `service_id` from the payload. It MUST NOT invent, drop, move, or retime assignments.

#### Scenario: Saint-Cloud week A
- **WHEN** the snapshot contains 92 assignments including Théo midi Monday 11:00–16:00
- **THEN** week A shows that shift on Théo’s midi Monday cell and empty cells stay empty

#### Scenario: Below-role post level is displayed, not scored
- **WHEN** an assignment’s `post_level` is lower than that employee’s role level
- **THEN** the grid shows the post level next to the duration and does not add, remove, or reclassify any warning

### Requirement: Warnings are displayed, never rescored
The client SHALL list every item in `planning.warnings` with its `severity`, and SHALL show the engine `message` (or an equivalent French presentation of the same `code` plus payload fields). Counts of issues on that list MUST match the array length. The client MUST NOT add, drop, merge, or re-severity warnings, and MUST NOT treat warning copy as a scoring rule.

#### Scenario: Hour shortfalls appear in the warning list
- **WHEN** the snapshot contains 14 `contract_hours` warnings and no `empty_post` warnings
- **THEN** the warnings list includes those 14 items and the client does not compute a different count from `stats`

#### Scenario: Engine English message is still the engine’s message
- **WHEN** a warning `message` is English
- **THEN** the restaurateur still sees that warning as engine output (French chrome around it is allowed; a new diagnosis is not)

### Requirement: Stats come from the snapshot, not from the UI
The client SHALL display `planning.stats` as returned: `assignments`, `empty`, `interdit`, `below_role`, `hours.percent` as the « Heures vs contrat » counter, and `wellbeing.held` / `wellbeing.total` as the « Souhaits bien-être » counter. It MUST NOT recompute those numbers from assignments, warnings, or wish rows. It MUST NOT display `hours.assigned`, `hours.contracted`, `stats.souhait`, or a « semaines à l’heure » counter (`weeks_ok` / `weeks_total` are absent). Wellbeing is wellbeing only, not contract hours.

#### Scenario: Counters match the engine
- **WHEN** `planning.stats` is `{ assignments: 92, empty: 0, interdit: 0, below_role: 43, hours: { percent: 84 }, wellbeing: { held: 21, total: 21 } }`
- **THEN** the recap shows 92, 0, 0, 43 / 92, 84 %, and 21 / 21, and does not show 416, 494, or a souhait count derived from warnings

### Requirement: Legal and wish tables are payload-driven
The client SHALL render the legal person×rule table from `planning.legal_rows` and column labels from `legal.rules` (`label_fr` / `id`). It SHALL render the wish table from `planning.wish_cols` and `planning.wish_rows`, including empty cells when a cell is null. Cell `ok` / `text` MUST be shown, not recalculated. A legal rule with no cells in any row MUST NOT be invented as a column.

#### Scenario: Salle legal columns
- **WHEN** legal context includes `max_daily_cuisine` but no `legal_rows` cell uses that id
- **THEN** the legal table omits cuisine 11 h/day and shows the engine texts for the rows that exist

#### Scenario: Wish contract under-hours
- **WHEN** a wish cell `contrat` has `ok: false` and text `30h · 29h / 39h`
- **THEN** that text appears in the Contrat column; the client does not change `ok`

### Requirement: French restaurateur chrome, read-only example
All product chrome (titles, section labels, loading and error copy, severity names) SHALL be French. The example grid without a company session MUST remain reachable without login. A `kind: employee` session MUST NOT show Mode édition.

#### Scenario: First useful screen
- **WHEN** the restaurateur opens the example screen on a desktop-width viewport with a valid snapshot
- **THEN** they can read week A, week B, the warning list, stats, legal table, and wish table

#### Scenario: Example without session
- **WHEN** nobody is logged in and they follow « Voir l’exemple »
- **THEN** the Saint-Cloud snapshot loads (92 assignments) even if auth returns 503

### Requirement: Login and register follow the auth contract
The client SHALL offer one login (email + password) via `POST /v1/auth/login` and SHALL take `kind` from `me` (no kind selector on login). Register SHALL live at `/register` with an **Entreprise** / **Salarié** toggle (never « restaurateur »). Entreprise SHALL send `{ kind: "company", email, password }` only. Salarié SHALL load fiches via `GET /v1/invites/{company_code}`, then send `{ kind: "employee", email, password, company_code, employee_id }` without `employee_token`. QR (`/register?company_code=&employee_token=`) SHALL lock Salarié, hide the fiche list, and POST `employee_token` without `employee_id`. Password MUST be ≥ 8. API `detail` SHALL be shown as-is. There MUST NOT be a « mot de passe oublié » control. Types MUST match the contract JSON; a missing key MUST throw.

#### Scenario: Company login
- **WHEN** a company account signs in
- **THEN** the client stores the token, shows email + Entreprise, and can call `GET /v1/me`

#### Scenario: Manual employee register
- **WHEN** a salarié enters a company code, picks a fiche, and submits email + password
- **THEN** register is `kind: employee` with `employee_id` and no token

#### Scenario: QR register
- **WHEN** the URL has `company_code` and `employee_token`
- **THEN** the form is locked to Salarié, lists no fiches, and commits with `employee_token`

### Requirement: Session token and logout
The token SHALL live in `sessionStorage`. `Authorization: Bearer` SHALL be sent on register/login/logout/`GET /v1/me` and GET/PATCH `/v1/context` when a token exists, and MUST NOT be sent on example or sandbox requests. Reload SHALL call `GET /v1/me` when a token exists; HTTP 401 SHALL forget the token and show login. **Déconnexion** SHALL `POST /v1/auth/logout` then forget the token. `kind: company` SHALL keep today’s grid + sandbox and MAY open `/context`. `kind: employee` SHALL hide Mode édition, MUST NOT open the context wizard, and SHALL show that the personal published planning comes later.

#### Scenario: Logout
- **WHEN** the restaurateur clicks Déconnexion
- **THEN** the token is forgotten and the login screen is shown

#### Scenario: Employee cannot edit
- **WHEN** `me.kind` is `employee`
- **THEN** Mode édition is absent, `/context` is not shown, and a French sentence says the personal published planning arrives later

### Requirement: Company context wizard
A `kind: company` session SHALL reach `/context` after login/register and via « Mon restaurant ». The client SHALL `GET /v1/context` and PATCH optional keys per `contracts/http/v1-context.md`. Identity SHALL show editable `name` (empty allowed), read-only « Droit du travail : France » from `legal_context_id`, and `company_code`. The wizard SHALL be sequential (roles → employees → services → types → typical week) then remain editable. Salle and cuisine SHALL be independent. Roles PATCH `ladders` with `substitution_explained: true`. Employees PATCH is the full list; show `invite_token` and the QR register URL; do not rotate. Services PATCH the restaurant list. Types PATCH the full list. Typical week PATCH `{ salle, cuisine }`; a closed cell is `closed: true` and `type_id` null. `ready.salle` / `ready.cuisine` SHALL be shown as returned (« Prêt à calculer » / « Pas encore prêt »). The client MUST NOT call generate or invent ready.

#### Scenario: Salle ready, cuisine not
- **WHEN** the restaurateur completes the five salle steps and leaves cuisine empty
- **THEN** the body has `ready.salle` true and `ready.cuisine` false

#### Scenario: Reload keeps context
- **WHEN** the restaurateur reloads `/context`
- **THEN** GET returns the same name, ladders, employees, services, types, and typical week

#### Scenario: Employee cannot open context
- **WHEN** `me.kind` is `employee`
- **THEN** the wizard is not shown
