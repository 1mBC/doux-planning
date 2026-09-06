## Purpose

Lets the restaurateur open a French web screen that shows the engine’s Saint-Cloud example snapshot: 14-day paper grid, warnings, stats, legal rows, and wish rows — plus login / register / session, a company context wizard, a published-cycle Calculer screen, live sandbox edit, and an employee team board — without scoring or deciding in the client.

## ADDED Requirements

### Requirement: Client loads only the example snapshot
The web client SHALL obtain restaurant, legal context, and planning data solely by calling `GET /v1/examples/saint-cloud`. It MUST NOT embed a second copy of the snapshot as source of truth, and MUST NOT invoke the constraint engine. Auth routes (`/v1/auth/*`, `/v1/me`, `/v1/invites/{company_code}`), `GET`/`PATCH /v1/context`, `POST /v1/generate`, `GET /v1/cycles`, `/v1/live/sandbox/{team}/*`, and `GET /v1/me/planning` MAY be called for session / company context / published cycles / live edit / employee board and MUST NOT feed the example grid. The client MUST NOT send `Authorization` on `/v1/examples/*` or `/v1/sandbox/*`.

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
- **WHEN** the snapshot contains 17 warnings including `contract_hours` and `consecutive_rest_days`
- **THEN** the warnings list length is 17 and the client does not compute a different count from `stats`

#### Scenario: Engine English message is still the engine’s message
- **WHEN** a warning `message` is English
- **THEN** the restaurateur still sees that warning as engine output (French chrome around it is allowed; a new diagnosis is not)

### Requirement: Stats come from the snapshot, not from the UI
The client SHALL display `planning.stats` as returned: `assignments`, `empty`, `interdit`, `below_role`, `hours.percent` as the « Heures vs contrat » counter, and `wellbeing.held` / `wellbeing.total` as the « Souhaits bien-être » counter. It MUST NOT recompute those numbers from assignments, warnings, or wish rows. It MUST NOT display `hours.assigned`, `hours.contracted`, `stats.souhait`, or a « semaines à l’heure » counter (`weeks_ok` / `weeks_total` are absent). Wellbeing is wellbeing only, not contract hours.

#### Scenario: Counters match the engine
- **WHEN** `planning.stats` is `{ assignments: 92, empty: 0, interdit: 0, below_role: 47, hours: { percent: 84 }, wellbeing: { held: 10, total: 12 } }`
- **THEN** the recap shows 92, 0, 0, 47 / 92, 84 %, and 10 / 12, and does not show 416, 494, or a souhait count derived from warnings

### Requirement: Legal and wish tables are payload-driven
The client SHALL render the legal person×rule table from `planning.legal_rows` and column labels from `legal.rules` (`label_fr` / `id`). It SHALL render the wish table from `planning.wish_cols` and `planning.wish_rows`, including empty cells when a cell is null. Cell `ok` / `text` MUST be shown, not recalculated. A legal rule with no cells in any row MUST NOT be invented as a column.

#### Scenario: Salle legal columns
- **WHEN** legal context includes `max_daily_cuisine` but no `legal_rows` cell uses that id
- **THEN** the legal table omits cuisine 11 h/day and shows the engine texts for the rows that exist

#### Scenario: Wish contract under-hours
- **WHEN** a wish cell `contrat` has `ok: false` and text `30h · 29h / 39h`
- **THEN** that text appears in the Contrat column (orange + bold); the client does not change `ok`

#### Scenario: Live wish columns on the public snapshot
- **WHEN** `wish_cols` uses live keys (`contrat`, `indispo`, `consecutive_rest`, `max_evening`, `max_coupures`, …)
- **THEN** those labels are shown and the client does not invent `we1j` / `weA` columns

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
The token SHALL live in `sessionStorage`. `Authorization: Bearer` SHALL be sent on register/login/logout/`GET /v1/me`, GET/PATCH `/v1/context`, `POST /v1/context/seed-example`, `GET /v1/context/export`, `POST /v1/context/import`, `POST /v1/generate`, `GET /v1/cycles`, `/v1/live/sandbox/{team}/*`, and `GET /v1/me/planning` when a token exists, and MUST NOT be sent on example or `/v1/sandbox/*` requests. Reload SHALL call `GET /v1/me` when a token exists; HTTP 401 SHALL forget the token and show login. **Déconnexion** SHALL `POST /v1/auth/logout` then forget the token. `kind: company` SHALL keep today’s grid + sandbox and MAY open `/context` and `/planning`. `kind: employee` SHALL hide Mode édition, MUST NOT open the context wizard, and SHALL open `/planning` via `GET /v1/me/planning`.

#### Scenario: Logout
- **WHEN** the restaurateur clicks Déconnexion
- **THEN** the token is forgotten and the login screen is shown

#### Scenario: Employee cannot edit
- **WHEN** `me.kind` is `employee`
- **THEN** Mode édition is absent on `/exemple`, `/context` is not shown, and `/planning` is the employee board (not Calculer / live)

### Requirement: Company context wizard
A `kind: company` session SHALL reach `/context` after login/register and via « Mon restaurant ». The client SHALL `GET /v1/context` and PATCH optional keys per `contracts/http/v1-context.md`. Identity SHALL show editable `name` (empty allowed), read-only « Droit du travail : France » from `legal_context_id`, and `company_code`. The wizard SHALL follow `contracts/domain/wizard-ui.md`: **Services → Rôles → Équipe → Souhaits bien-être → Services types → Semaine type**, then remain editable. The « Fiches » and lone « Types » labels MUST NOT appear. An empty `services` list SHALL keep the client on Services. Unchecking a service MUST confirm in one French sentence then purge types, typical-week cells, unavailabilities, and `max_services` keys for that service on **both** teams, and PATCH the cleaned `services` + `employees` + `types` + `typical_week`. A service not offered MUST be invisible (no fallback to the three ids). The wellbeing tab MUST NOT be a `ready` prerequisite. Wishes SHALL be the `Wellbeing` object (`consecutive_rest`, required bool `weekend_rest_day` next to the weekend radio and cumulable with it, `max_services` only for offered services, `max_coupures_per_week`). An old list key `at_least_one_weekend_rest_day` MUST throw. Services types SHALL use one sub-tab per offered service, **Ajouter un type** at the bottom, a chronological **one-line** list of arrivals and departures (add either, trash at end), +/− counters per ladder level (no `;` / comma), a **STAFF après** column, and worst-case `remaining_post_levels`. Employees PATCH is the full list; each team row SHALL show name, role, contract hours, `min_shift_hours`, a French unavailability summary, and QR / `invite_token`. Adding an unavailability SHALL open a popup of weekday × **offered** service checkboxes and append `{ weekday, service_id }` slots. `week_labels` SHALL drive A/B vs Paire/Impaire on the typical-week chrome and on `/planning` grids. Salle and cuisine SHALL be independent. Roles PATCH `ladders` with `substitution_explained: true`. Typical week PATCH `{ salle, cuisine }`; a closed cell is `closed: true` and `type_id` null. `ready.salle` / `ready.cuisine` SHALL be shown as returned (« Prêt à calculer » / « Pas encore prêt »). The client MUST NOT call generate or invent ready.

#### Scenario: Services first then purge morning
- **WHEN** the restaurateur starts `/context` then later unchecks petit-déjeuner after types exist
- **THEN** a French confirm is shown and morning disappears from types, typical week, indispos, and max_services

#### Scenario: Salle ready, cuisine not
- **WHEN** the restaurateur completes the salle steps and leaves cuisine empty
- **THEN** the body has `ready.salle` true and `ready.cuisine` false

#### Scenario: Reload keeps context
- **WHEN** the restaurateur reloads `/context`
- **THEN** GET returns the same name, ladders, employees, services, types, and typical week

#### Scenario: Employee cannot open context
- **WHEN** `me.kind` is `employee`
- **THEN** the wizard is not shown

### Requirement: Seed example on company context
A `kind: company` session on `/context` SHALL show **Intégrer l’exemple Saint-Cloud** next to the company code, whether the restaurant is empty or already filled. The button MUST ask for a one-sentence French confirm (replaces roles, team, wishes, types, week; keeps the name; breaks linked employee accounts; does not paste the example planning) before `POST /v1/context/seed-example` with Bearer and no body. A 200 SHALL replace the wizard state via the same Context parse as GET. API `detail` SHALL be shown on error. The client MUST stay on `/context` and MUST NOT call generate. The button MUST NOT appear for employees, on `/exemple`, `/planning`, or login.

#### Scenario: Empty company seeds Saint-Cloud context
- **WHEN** a company account confirms the seed
- **THEN** GET-shaped Context has salle ready, cuisine not ready, example fiches, `week_labels` `"ab"`, and the restaurant name unchanged

#### Scenario: Second seed overwrites
- **WHEN** the restaurateur confirms seed again
- **THEN** the wizard again shows the example fiches (previous edits are gone)

### Requirement: Export and import restaurant config
A `kind: company` session on `/context` SHALL show **Exporter la config** and **Importer une config** on the same `seed-row` as **Intégrer l’exemple Saint-Cloud**. **Exporter** SHALL `GET /v1/context/export` with Bearer, parse the freeze (`export_version` MUST be `1` or throw; `invite_token` / `company_code` MUST NOT be required), and download JSON as `{name}-config.json` or `config-resto.json`. **Importer** SHALL accept a `.json` file, ask for a one-sentence French confirm (replaces name, roles, team, wishes, types, week; breaks linked employee accounts; does not paste a planning), then `POST /v1/context/import` with the parsed object. A 200 SHALL `adopt` the wizard via the same Context parse as GET. Dismissing the confirm MUST be a no-op (no POST). API `detail` SHALL be shown on error. The buttons MUST NOT appear for employees, on `/exemple`, `/planning`, or login. The client MUST NOT offer planning exports.

#### Scenario: Company exports version-1 JSON without tokens
- **WHEN** the restaurateur clicks **Exporter la config**
- **THEN** a JSON file downloads with `export_version` 1 and no `invite_token`

#### Scenario: Import plus confirm replaces the wizard
- **WHEN** the restaurateur picks a valid export JSON and confirms
- **THEN** the wizard shows the imported name, roles, team, wishes, types, and week, and a reload still has that context

#### Scenario: Cancel import confirm is a no-op
- **WHEN** the restaurateur picks a file then dismisses the confirm
- **THEN** the client MUST NOT POST `/v1/context/import` and the wizard stays unchanged

### Requirement: Company published cycle
A `kind: company` session SHALL reach `/planning` via « Planning ». The client SHALL `GET /v1/cycles` and `GET /v1/context` on load. Types MUST match `contracts/http/v1-generate.md` (and context) JSON; a missing key MUST throw. **Calculer** SHALL be enabled only when `ready[team]` from context is true, and SHALL `POST /v1/generate` with `{ team, search_effort: "minimal" }`. If `ready[team]` is false the button MUST be disabled and the client MUST NOT POST. API `detail` SHALL be shown on 409/400. When `published[team]` is not null the client SHALL parse `stats`, `legal_cols`, `legal_rows`, `wish_cols`, and `wish_rows` (a missing key MUST throw) and SHALL render a 14-day paper grid (A/B or Paire/Impaire from `week_labels`) from that team’s context fiches plus `assignments`, list every `warnings` item (engine `message` as-is, French severity), and — unless Mode édition is open — show stats pastilles plus **Règles légales** / **Souhaits bien-être** tables from those recap keys (`text` as-is; wish cell `null` = empty; cell `ok: false` orange + bold, including `contrat`). Warning `code === contract_hours` SHALL show pastille **Contrat**; other `severity: souhait` stay « Souhait ». **Calculer** and **Mode édition** SHALL sit under the Salle · Cuisine switch, not on the same row. Mode édition MUST hide the recaps (grid + warnings + history only). The client MUST NOT invent recap numbers or `we1j` / `weA` columns. Regenerating SHALL replace that team only. Reload SHALL use the same GET. When `published[team]` exists the client MAY offer Mode édition via the live sandbox routes. No planning exports.

#### Scenario: Salle calculated, cuisine not
- **WHEN** salle is ready and the restaurateur clicks Calculer, while cuisine is not ready
- **THEN** `published.salle` has assignments, recap pastilles + legal/wish tables, and any engine warnings on the salle grid, cuisine shows « Pas encore calculé », and Calculer is disabled on cuisine

#### Scenario: Edit mode hides recaps
- **WHEN** Mode édition is open on a published team
- **THEN** stats pastilles and legal/wish tables are hidden; the grid, warnings, and history remain

#### Scenario: Reload keeps published salle
- **WHEN** the restaurateur reloads `/planning` after a salle generate
- **THEN** GET `/v1/cycles` still has the salle cycle and cuisine remains null

#### Scenario: Employee cannot open company planning
- **WHEN** `me.kind` is `employee`
- **THEN** the company published-cycle screen (Calculer / Mode édition) is not shown

### Requirement: Employee published board
A `kind: employee` session SHALL reach `/planning` after login/register and via « Planning ». The client SHALL `GET /v1/me/planning` with Bearer. Types MUST match `contracts/http/v1-me-planning.md` JSON; a missing key MUST throw. API `detail` SHALL be shown as-is. The client SHALL render a 14-day paper grid from `employees` + `assignments` of that employee’s team, titled A/B or Paire/Impaire from `week_labels`. Rows whose `employee_id` equals `me` (`employee_id` on the payload) SHALL be highlighted; other teammates SHALL stay visible but muted. Empty `assignments` SHALL show « Pas encore publié » instead of a fake grid. A read-only panel SHALL show `contract` (`weekly` / `assigned` / `ok`), `unavailabilities` `{ weekday, service_id }`, and `wishes` `{ kind, held, … }` with French labels and tenu / non tenu (`weekend_rest_day` → « Au moins un repos samedi ou dimanche »). The client MUST NOT invent `wish_rows` or `key` fields, MUST NOT offer Calculer, Mode édition, the context wizard, generate, or live sandbox, and MUST NOT edit wishes or unavailabilities.

#### Scenario: Published salle teammate grid
- **WHEN** a salarié linked to a published salle fiche opens `/planning`
- **THEN** the grid lists that team’s employees and assignments, the salarié’s rows are colored, colleagues are muted, and the contract / wishes panel shows payload values

#### Scenario: No published cycle
- **WHEN** `assignments` is empty
- **THEN** the screen shows « Pas encore publié » and still shows the contract panel from the payload

### Requirement: Live sandbox on published cycle
A `kind: company` session on `/planning` SHALL show **Mode édition** only when `published[team]` is not null. The button SHALL `POST /v1/live/sandbox/{team}/enter` with Bearer and MUST NOT call `/v1/sandbox/*`. LiveState MUST include `team`; a missing key MUST throw. Edit UX SHALL match the example sandbox: occupied overlay (retune ±15 Valider, replace, swap), empty-cell fill, API `detail`, history, **Annuler**, **Tout annuler** (discard). **Lecture** SHALL leave the edit UI without discard. Re-entering SHALL keep the draft cran (GET/enter live). **Publier** SHALL `POST .../publish`, leave edit UI, and show the updated `published` from that body or GET `/v1/cycles`. The other team MUST stay intact. `/exemple` SHALL keep calling `/v1/sandbox/*` without Bearer.

#### Scenario: Retune then publish
- **WHEN** salle is published, the restaurateur enters live edit, validates a retune, leaves via Lecture, re-enters, then Publier
- **THEN** the cran is still present after Lecture + re-enter, and after Publier + reload GET `/v1/cycles` matches the edited assignments

#### Scenario: Cuisine without cycle
- **WHEN** cuisine has no published cycle
- **THEN** Mode édition is not offered for cuisine (API would 409)

#### Scenario: Example joujou stays public
- **WHEN** nobody is logged in and they open Mode édition on `/exemple`
- **THEN** `POST /v1/sandbox/enter` still returns 200 and the snapshot still has 92 assignments

### Requirement: Chrome polish on recaps and wizard
`/planning` company and `/exemple` SHALL use the same recap chrome: `contract_hours` pastille **Contrat**, `ok: false` cells orange + bold, wish table title **Souhaits bien-être**, engine `message` as-is. `/exemple` MUST NOT rewrite the snapshot. Services types SHALL keep clock and ±15 on one line, show bag / error only for STAFF, and a labeled N counter, as **cards** (no `wave-table`). Roles SHALL use Nom + Niveau stepper. Weekend-rest SHALL have its own `<th>` **Au moins un repos samedi ou dimanche** (checkbox not inside the Week-end cell). Company identity SHALL offer **Inviter mes employés** (display and copy the absolute `origin + /register?company_code={code}` + QR of that URL) and MUST hide invite tokens / URLs under fiches.

#### Scenario: Contract warning uses Contrat pill
- **WHEN** a published cycle lists a `contract_hours` warning
- **THEN** that row’s severity pastille is **Contrat** and other `souhait` warnings still say **Souhait**

#### Scenario: Bad recap cells are orange
- **WHEN** a legal or wish cell has `ok: false`
- **THEN** that cell (not only the row’s first column) is orange and bold, including `contrat`

#### Scenario: Invite popup shows URL and QR
- **WHEN** the restaurateur clicks **Inviter mes employés**
- **THEN** a popup displays and copies the absolute `origin + /register?company_code={code}` and shows a QR of that same URL, without exposing per-fiche tokens

#### Scenario: Types are cards not a spreadsheet
- **WHEN** the restaurateur opens Services types
- **THEN** events render as `wave-line` cards under short labels (Heure · N · Niveaux · STAFF après) and no `wave-table` is present

#### Scenario: Weekend rest has its own column
- **WHEN** the restaurateur opens Souhaits bien-être
- **THEN** the weekend-rest checkbox sits under its own header and not inside the Week-end cell
