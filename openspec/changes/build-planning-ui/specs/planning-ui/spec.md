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
The token SHALL live in `sessionStorage`. `Authorization: Bearer` SHALL be sent on register/login/logout/`GET /v1/me`, GET/PATCH `/v1/context`, `POST /v1/context/seed-example`, `GET /v1/context/export`, `POST /v1/context/import`, `DELETE /v1/staff/{id}`, `POST /v1/auth/link`, `POST /v1/generate`, `GET /v1/cycles`, `/v1/live/sandbox/{team}/*`, `GET /v1/me/planning`, and `GET /v1/admin/generates` when a token exists, and MUST NOT be sent on example or `/v1/sandbox/*` requests. Reload SHALL call `GET /v1/me` when a token exists; HTTP 401 SHALL forget the token and show login. **Déconnexion** SHALL `POST /v1/auth/logout` then forget the token. `kind: company` SHALL keep today’s grid + sandbox and MAY open `/context` and `/planning`. `kind: employee` SHALL hide Mode édition and MUST NOT open the context wizard. An affiliated employee (`employee_id` string) SHALL open `/planning` via `GET /v1/me/planning`. An unaffiliated employee (`kind: employee` and `employee_id === null`) MUST NOT open `/planning` and MUST NOT see a chrome « Planning » link. `parseMe` MUST require `admin` as a boolean; `kind: employee` SHALL force `admin` false. `parseMe` MUST accept `restaurant_id: string | null` (`kind: company` → string; affiliated employee → both strings; unaffiliated employee → both `null`). The session chrome SHALL show **Admin** only when `me.admin` is true.

#### Scenario: Logout
- **WHEN** the restaurateur clicks Déconnexion
- **THEN** the token is forgotten and the login screen is shown

#### Scenario: Employee cannot edit
- **WHEN** `me.kind` is `employee` and `employee_id` is a string
- **THEN** Mode édition is absent on `/exemple`, `/context` is not shown, and `/planning` is the employee board (not Calculer / live)

#### Scenario: Unaffiliated employee has no Planning link
- **WHEN** `me.kind` is `employee` and `employee_id` is `null`
- **THEN** the session chrome has no « Planning » button and `/planning` is not the team grid

### Requirement: Company context wizard
A `kind: company` session SHALL reach `/context` after login/register and via « Mon restaurant ». The client SHALL `GET /v1/context` and PATCH optional keys per `contracts/http/v1-context.md`. Identity SHALL show editable `name` (empty allowed), read-only « Droit du travail : France » from `legal_context_id`, and `company_code`. The wizard SHALL follow `contracts/domain/wizard-ui.md`: **Services → Rôles → Équipe → Souhaits bien-être → Services types → Semaine type**, then remain editable. The « Fiches » and lone « Types » labels MUST NOT appear. An empty `services` list SHALL keep the client on Services. Unchecking a service MUST confirm in one French sentence then purge types, typical-week cells, unavailabilities, `max_services` keys, and `min_shift_hours` keys for that service on **both** teams, and PATCH the cleaned `services` + `employees` + `types` + `typical_week`. A service not offered MUST be invisible (no fallback to the three ids). The wellbeing tab MUST NOT be a `ready` prerequisite. Wishes SHALL be the `Wellbeing` object (`consecutive_rest`, required bool `weekend_rest_day` next to the weekend radio and cumulable with it, `max_services` only for offered services, `max_coupures_per_week`). An old list key `at_least_one_weekend_rest_day` MUST throw. Offered-service **display order** on Services types sub-tabs and typical-week columns SHALL be `CONTEXT_SERVICES.filter(s => offered.includes(s.id))` (morning → midday → evening). The client MUST NOT use `services.map` for that display order; persist `services[]` order SHALL stay as saved. Services types SHALL use one sub-tab per offered service, **Ajouter un type** at the bottom, **one `<table>` per type sheet** (chronological Arrivée | **Départ** rows, no `wave-line` cards), compact steppers for ±15 / levels, a **STAFF minimal resultant** column (bag / error), and worst-case `remaining_post_levels`. Employees PATCH is the full list for edits; each team row SHALL show name, role, contract hours, one `min_shift_hours` `Stepper` per offered service (`CONTEXT_SERVICES.filter`, default 4, `step={0.5}`, `min={0.5}`), unavailability chips, and a trash control (same chrome as roles). `min_shift_hours` SHALL be a sparse `Record<string, number>`. GET MAY still return a number until Infra ships (coerce `4` to `{}`, other N onto every offered service). PATCH SHALL send the object. An unoffered service MUST have no stepper and no map key. A new employee row SHALL start offered services at 4. Deleting a fiche SHALL follow `contracts/domain/delete-employee.md`. Invite tokens / per-fiche QR MUST stay hidden. Adding an unavailability SHALL open a popup of weekday × **offered** service checkboxes and append `{ weekday, service_id }` slots. `week_labels` SHALL drive A/B vs Paire/Impaire on the typical-week chrome and on `/planning` grids. Salle and cuisine SHALL be independent. Roles PATCH `ladders` with `substitution_explained: true`. Typical week PATCH `{ salle, cuisine }`; a closed cell is `closed: true` and `type_id` null. `ready.salle` / `ready.cuisine` SHALL be shown as returned (« Prêt à calculer » / « Pas encore prêt »). The client MUST NOT call generate or invent ready.

#### Scenario: Services first then purge morning
- **WHEN** the restaurateur starts `/context` then later unchecks petit-déjeuner after types exist
- **THEN** a French confirm is shown and morning disappears from types, typical week, indispos, max_services, and min_shift_hours keys

#### Scenario: Salle ready, cuisine not
- **WHEN** the restaurateur completes the salle steps and leaves cuisine empty
- **THEN** the body has `ready.salle` true and `ready.cuisine` false

#### Scenario: Reload keeps context
- **WHEN** the restaurateur reloads `/context`
- **THEN** GET returns the same name, ladders, employees, services, types, and typical week

#### Scenario: Employee cannot open context
- **WHEN** `me.kind` is `employee`
- **THEN** the wizard is not shown

#### Scenario: Min shift steppers follow offered services
- **WHEN** the restaurant offers morning, midday, and evening
- **THEN** each Équipe fiche shows three min-shift steppers (Petit-déjeuner → Déjeuner → Dîner) defaulting to 4, with no unique number input

#### Scenario: Scalar GET min_shift_hours is coerced
- **WHEN** GET `employees[].min_shift_hours` is the number `3`
- **THEN** each offered-service stepper shows 3

#### Scenario: Unoffered service has no min-shift stepper
- **WHEN** petit-déjeuner is not offered
- **THEN** Équipe has no morning stepper and no `morning` key on `min_shift_hours`

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
A `kind: company` session SHALL reach `/planning` via « Planning ». The client SHALL `GET /v1/cycles` and `GET /v1/context` on load. Types MUST match `contracts/http/v1-generate.md` + `generate-versions.md` JSON (`published[team].versions` + `latest` ; a missing **required** 3-effort key MUST throw). Chrome SHALL be **three rows** : Salle | Cuisine (blue = team) ; Minimal | Optimisé | Maximal | **Manuel** (blue = **selection**, no POST, default `latest`) ; white actions **(Re)Calculer le planning** (compute slots only), **Entrer en mode édition**, **Quitter le mode édition**, **Publier**, **Exporter**. Recalculer SHALL POST the **selected** compute `search_effort` only when `ready[team]` is true, Mode édition is closed, and the selected slot is not `manuel`. The client MUST NOT call `postGenerate` with `"manuel"`. Minimal / Optimisé wait for 200 ; Maximal accepts 202 then polls `GET /v1/generate/jobs/{id}` until `done` / `failed`. Loader overlay ≥ 1 s. An empty **compute** slot SHALL show « Pas encore calculé » and MUST NOT fall back to another version. Under row 3 the client SHALL show that cycle’s `generated_at` in `Europe/Paris` (absent → tiret). Clicking Minimal / Optimisé / Maximal / Manuel MUST NOT POST generate. If `ready[team]` is false Recalculer MUST be disabled and the client MUST NOT POST. API `detail` SHALL be shown on 409/400. When the selected version is not null the client SHALL parse recap keys (throw if missing) and SHALL render the 14-day paper grid from that version’s `assignments`, list every `warnings` item, and — unless Mode édition is open — show stats pastilles plus legal / wish tables. Mode édition on a compute slot SHALL `POST /v1/live/sandbox/{team}/enter` with the selected `search_effort` and MUST hide the recaps. Export SHALL use the displayed version. The client MUST NOT invent recap numbers. Regenerating SHALL write only that team’s selected compute slot. Reload SHALL use GET. Employee `/planning` MUST NOT show the effort selector. Manuel chrome SHALL follow Requirement: Manual planning slot.

#### Scenario: Salle calculated, cuisine not
- **WHEN** salle is ready and the restaurateur selects Minimal then clicks (Re)Calculer, while cuisine is not ready
- **THEN** `published.salle.versions.minimal` has assignments and recaps, cuisine shows « Pas encore calculé », and Recalculer is disabled on cuisine

#### Scenario: Edit mode hides recaps
- **WHEN** Mode édition is open on a published team
- **THEN** stats pastilles and legal/wish tables are hidden; the grid, warnings, and history remain

#### Scenario: Reload keeps published salle
- **WHEN** the restaurateur reloads `/planning` after a salle generate
- **THEN** GET `/v1/cycles` still has the salle cycle and cuisine remains null

#### Scenario: Employee cannot open company planning
- **WHEN** `me.kind` is `employee`
- **THEN** the company published-cycle screen (Calculer / Mode édition) is not shown

### Requirement: Export published planning
A `kind: company` session on `/planning` SHALL show a menu **Exporter** (JSON / CSV / XLSX / JPEG) in `planning-actions` under Salle · Cuisine. The menu SHALL be enabled only when `published[team]` is not null and Mode édition is closed. Cuisine `null` or Mode édition SHALL disable the menu. Export SHALL be client-side from the already-loaded cycle plus that team’s fiches (no `invite_token`); the client MUST NOT call a new HTTP route. JSON SHALL be `{ export_version: 1, kind: "planning", team, restaurant_name, week_labels, employees, assignments, warnings, stats, legal_cols, legal_rows, wish_cols, wish_rows }`. CSV SHALL stay a flat grid (personne, jour, service, début, fin, heures) plus metadata. XLSX SHALL NOT be that CSV dump: it SHALL have **two sheets** (Semaine A / B or Paire / Impaire), a title **Planning validé en date du :** plus the local export timestamp, days Lun–Dim each with DEBUT / FIN / NB HEURES, and **one row per person × offered service** (`morning` / `midday` / `evening` from `context.services`, labels PDJ / DJ / Dîner). JPEG SHALL show both week sheets at ≥ 2× CSS pixels (`devicePixelRatio`), with a readable font and JPEG `quality` ≥ 0.95. Filename `{name-slug}-{salle|cuisine}.{json|csv|xlsx|jpg}` (`name` empty → `planning`). Numbers and warning `message` MUST come from the payload. The menu MUST NOT appear for employees or on `/exemple`.

#### Scenario: Company exports published salle JSON
- **WHEN** salle is published and the restaurateur chooses JSON
- **THEN** a file downloads with `export_version` 1 and `kind` `"planning"`

#### Scenario: Cuisine null disables export
- **WHEN** `published.cuisine` is null
- **THEN** the Exporter menu is disabled on cuisine

#### Scenario: Edit mode disables export
- **WHEN** Mode édition is open
- **THEN** the Exporter menu is disabled

### Requirement: Employee published board
A `kind: employee` session with a non-null `employee_id` SHALL reach `/planning` after login/register and via « Planning ». The client SHALL `GET /v1/me/planning` with Bearer. Types MUST match `contracts/http/v1-me-planning.md` JSON; a missing key MUST throw. API `detail` SHALL be shown as-is. The client SHALL render a 14-day paper grid from `employees` + `assignments` of that employee’s team, titled A/B or Paire/Impaire from `week_labels`. Rows whose `employee_id` equals `me` (`employee_id` on the payload) SHALL be highlighted; other teammates SHALL stay visible but muted. Empty `assignments` SHALL show « Pas encore publié » instead of a fake grid. A read-only panel SHALL show `contract` (`weekly` / `assigned` / `ok`), `unavailabilities` `{ weekday, service_id }`, and `wishes` `{ kind, held, … }` with French labels and tenu / non tenu (`weekend_rest_day` → « Au moins un repos samedi ou dimanche »). The client MUST NOT invent `wish_rows` or `key` fields, MUST NOT offer Calculer, Mode édition, the context wizard, generate, or live sandbox, and MUST NOT edit wishes or unavailabilities.

#### Scenario: Published salle teammate grid
- **WHEN** a salarié linked to a published salle fiche opens `/planning`
- **THEN** the grid lists that team’s employees and assignments, the salarié’s rows are colored, colleagues are muted, and the contract / wishes panel shows payload values

#### Scenario: No published cycle
- **WHEN** `assignments` is empty
- **THEN** the screen shows « Pas encore publié » and still shows the contract panel from the payload

### Requirement: Live sandbox on published cycle
A `kind: company` session on `/planning` SHALL show **Mode édition** on a **compute** slot only when that slot’s cycle is not null. On **Manuel**, the button SHALL follow Requirement: Manual planning slot (`ready[team]`, even if `versions.manuel` is null). The button SHALL `POST /v1/live/sandbox/{team}/enter` with Bearer and MUST NOT call `/v1/sandbox/*`. LiveState MUST include `team`; a missing key MUST throw. Edit UX SHALL match the example sandbox: occupied overlay (retune ±15 Valider, replace, swap), empty-cell fill, API `detail`, history, **Annuler**, **Tout annuler** (discard). **Lecture** SHALL leave the edit UI without discard. Re-entering SHALL keep the draft cran (GET/enter live). **Publier** SHALL `POST .../publish`, leave edit UI, and show the updated `published` from that body or GET `/v1/cycles`. The other team MUST stay intact. `/exemple` SHALL keep calling `/v1/sandbox/*` without Bearer.

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
`/planning` company and `/exemple` SHALL use the same recap chrome: `contract_hours` pastille **Contrat**, `ok: false` cells orange + bold, wish table title **Souhaits bien-être**, engine `message` as-is. `/exemple` MUST NOT rewrite the snapshot. Services types SHALL use **one `<table>` per type sheet** (no `wave-line` cards) with columns Type (Arrivée | **Départ**), Heure (time-dial overlay + compact ±15 stepper), **Niveaux minimal requis (par arrivée | après départ)**, and **STAFF minimal resultant** (bag / error only) — **no N column**. Roles, types levels, overlay sandbox, and ±15 SHALL share the same **framed** stepper chrome (bold label, centered value). Weekend-rest SHALL have its own `<th>` **Au moins un repos samedi ou dimanche** (checkbox not inside the Week-end cell). Company identity SHALL offer **Inviter mes employés** (display and copy the `company_code` **and** the absolute `origin + /register?company_code={code}` + QR of that URL) and MUST hide invite tokens / URLs under fiches. Roles SHALL be a `<table>` (Nom / Niveau stepper / trash) ; deleting a role MUST confirm in French, list matching fiches, say they will need review / recalc, and advise renaming instead. Équipe MUST NOT show a subtitle or a text line of unavailabilities (chips only). Souhaits MUST NOT show a subtitle. Services types MUST NOT say « Sous-onglets = services offerts ». Semaine type MUST NOT say « Libellés de cycle… » nor « L’autre équipe est renvoyée… ».

#### Scenario: Contract warning uses Contrat pill
- **WHEN** a published cycle lists a `contract_hours` warning
- **THEN** that row’s severity pastille is **Contrat** and other `souhait` warnings still say **Souhait**

#### Scenario: Bad recap cells are orange
- **WHEN** a legal or wish cell has `ok: false`
- **THEN** that cell (not only the row’s first column) is orange and bold, including `contrat`

#### Scenario: Invite popup shows URL and QR
- **WHEN** the restaurateur clicks **Inviter mes employés**
- **THEN** a popup displays the `company_code` (copyable) and copies the absolute `origin + /register?company_code={code}` and shows a QR of that same URL, without exposing per-fiche tokens

#### Scenario: Roles are a table with confirm delete
- **WHEN** the restaurateur opens Rôles and clicks the trash on a role that fiches still use
- **THEN** a French confirm lists those fiches, says they will need review / recalc, advises renaming, and only then removes the row without changing fiches until save

#### Scenario: Types are a table per sheet
- **WHEN** the restaurateur opens Services types
- **THEN** each type is a `<table>` with Type · Heure · Niveaux minimal requis · STAFF and no N column and no `wave-line` cards, and the Type cell / thead say **Départ** (not Sortie)

#### Scenario: Weekend rest has its own column
- **WHEN** the restaurateur opens Souhaits bien-être
- **THEN** the weekend-rest checkbox sits under its own header and not inside the Week-end cell

### Requirement: Admin generate table
A session with `me.admin === true` SHALL see an **Admin** chrome link and MAY open `/admin`. That page SHALL `GET /v1/admin/generates` with Bearer and render `{ entries }` newest-first, grouped by calendar day in `Europe/Paris` (`created_at`) with a heading like `Dimanche 6 septembre 2026`. Days without a row MUST NOT appear. Each row SHALL show Paris `HH:mm`, email, restaurant name, team (Salle / Cuisine), **effort** (Minimal / Optimisé / Maximal, dash if null), and **duration** (`Ns` / `N min`, dash if null). Hovering a row or its warning count SHALL show **one card per warning** with the same richness as the planning recap (severity, title, day + week A/B, `employee_name`, `message`; missing fields → dash), or `aucun warning` when the array is empty. The page MUST NOT list warnings in a panel under the table. An empty `entries` list SHALL show « Aucun generate pour l’instant. ». If `me.admin` is not true (anonymous, employee, or company without admin), `/admin` SHALL show `Action réservée à l’admin.` and MUST NOT call `GET /v1/admin/generates`. The Admin link MUST NOT appear unless `me.admin` is true. The table MUST NOT appear on employee, `/exemple`, or `/planning`.

#### Scenario: Admin sees two day headers
- **WHEN** an admin opens `/admin` and the payload has entries on two distinct Paris days
- **THEN** the table shows exactly two day headings

#### Scenario: Hover shows warning cards
- **WHEN** the admin hovers a row whose `warnings` is not empty
- **THEN** each warning is a card with severity, title, day + week, person, and `message` (not the message alone)

#### Scenario: Non-admin does not fetch generates
- **WHEN** a company without admin, a salarié, or an anonymous visitor opens `/admin`
- **THEN** the reserved message is shown and the client does not GET `/v1/admin/generates`

### Requirement: Three generate efforts
Company `/planning` SHALL show **Minimal**, **Optimisé**, **Maximal**, and **Manuel** as a **selection** row (default `latest`). POST generate SHALL happen only from **(Re)Calculer le planning** and only for the three compute efforts. Minimal / Optimisé sync ; Maximal 202 + poll. Loader ≥ 1 s. Under the timestamp the client SHALL show the displayed slot’s `duration_seconds` (dash if absent; Manuel: dash when absent, no `engine_ref`). Employee `/planning` and `/exemple` MUST NOT offer the selector. Recalculer is hidden on Manuel and off in Mode édition.

#### Scenario: Selecting Minimal then Optimisé switches the grid
- **WHEN** salle has both `versions.minimal` and `versions.optimized`
- **THEN** clicking Minimal then Optimisé changes the displayed grid and `generated_at` without POSTing

#### Scenario: Recalculer posts the selected effort
- **WHEN** salle is ready, Optimisé is selected, and the restaurateur clicks (Re)Calculer le planning
- **THEN** the client POSTs `{ team: "salle", search_effort: "optimized" }`

#### Scenario: Maximal polls until the grid updates
- **WHEN** salle is ready, Maximal is selected, and the restaurateur clicks (Re)Calculer le planning
- **THEN** the client POSTs `{ team: "salle", search_effort: "maximal" }`, receives 202 without `published`, polls the job until `done`, and then shows that version’s grid

#### Scenario: Edit mode turns generate off
- **WHEN** Mode édition is open
- **THEN** Recalculer is disabled and clicking Minimal / Optimisé / Maximal does not POST

### Requirement: Cycle score notes
Company `/planning` SHALL display the five axis notes and `global` from `score` of the **currently displayed** cycle (selected effort). Each note SHALL be one French decimal (`8,4`) or a dash when `null` / absent. The client MUST NOT recompute notes, MUST NOT show or edit `weights`, and MUST NOT offer an admin bench. Employee `/planning` MUST NOT show these notes. `/exemple` SHALL show them only when the snapshot payload includes `score`.

#### Scenario: Notes follow the displayed slot
- **WHEN** salle has both `versions.minimal` and `versions.optimized` with different `score.global`
- **THEN** clicking Minimal then Optimisé changes the displayed notes to that slot without POSTing

#### Scenario: Null note is a dash
- **WHEN** a displayed cycle has `score.notes.wellbeing` null
- **THEN** that pastille shows `—` and does not invent a number

### Requirement: Cycle score chrome
Company `/planning` and `/exemple` SHALL place the `CycleScoreNotes` row **above** the grid and MUST NOT render the old `CycleStats` / `Stats` cards (shifts, empty posts, legal alerts, below-role, hours percent, wellbeing counts). `LegalRecap` / `WishRecap` SHALL stay **below** the grid, unchanged. The `contrat` axis label SHALL be **Occupation /10** (JSON key `contrat` unchanged). Each axis pill SHALL show `resumes[key]` as-is underneath; the global pill SHALL have no subtitle. Color SHALL be linear HSL `hue = 12 × note` (0 red → 120 green); `null` SHALL be a dash with no tint. The parser MUST require `resumes` (five keys, `string | null`); a `score` payload without `resumes` SHALL omit the notes row and MUST NOT crash. The client MUST NOT edit `weights` or offer an admin bench.

#### Scenario: Occupation label and resumes
- **WHEN** a displayed cycle has `score.notes` and `score.resumes`
- **THEN** the contrat pill is labeled Occupation /10, each axis shows its `resumes` string, and Globale has no subtitle

#### Scenario: Missing resumes omits notes
- **WHEN** a cycle `score` object has no `resumes` key
- **THEN** the notes row is omitted and the page still renders

#### Scenario: Effort switch updates notes and resumes
- **WHEN** salle has both `versions.minimal` and `versions.optimized` with different `score` notes and resumes
- **THEN** clicking Minimal then Optimisé shows that slot’s notes and resumes without POSTing

### Requirement: Cycle score gauges
Company `/planning` and `/exemple` SHALL show **Globale /10 first, on the left**, with a contrasted frame (thicker border, more saturated fill, same HSL hue) and no resume under it. Each of the six pills SHALL include a horizontal gauge under the number whose fill width is `note / 10` and whose hue is `12 × note`; a `null` note SHALL show an empty neutral gauge. Axis `resumes` SHALL keep `\n` (`white-space: pre-line`). Labels stay Occupation / Couverture / Légal / Bien-être / Rôles / Globale, all `/10`. No stats cards. Legal / wish tables stay under the grid.

#### Scenario: Globale leads the row
- **WHEN** a displayed cycle has `score`
- **THEN** the first pastille is Globale /10, it has no resume, and it is visually more contrasted than the five axes

#### Scenario: Gauges follow the note
- **WHEN** a pastille has note `9,2`
- **THEN** its gauge fill is 92 % wide at hue `12 × 9.2`

#### Scenario: Occupation resume is two lines
- **WHEN** `score.resumes.contrat` contains a newline with `occupées` then indispos
- **THEN** the Occupation pill shows both lines (hours then indispos)

### Requirement: Admin bench table and compare
Company `me.admin` SHALL see a **Banc** link on `/admin` (generate log stays). `/admin/bench` SHALL load datasets and runs, offer launch all / category / dataset × Minimal / Optimisé / Maximal, and show one table row per dataset with the **latest** run per effort as generated global · oracle global · Δ global (dash if none). Clicking an effort cell SHALL open `/admin/bench/{category}/{id}/{effort}`. `dataset` + `minimal`/`optimized` is HTTP 200 ; `all` / `category` / `maximal` is 202 and the client MAY poll jobs or refresh runs (leaving the page is OK). The compare page SHALL title `category · id · effort`, show the generated planning then the oracle (notes + resumes, read-only grids). Empty / 404 SHALL be a French message. Non-admin `/admin` and `/admin/bench` SHALL show `Action réservée à l’admin.` without calling bench APIs.

#### Scenario: Minimal dataset run fills the table
- **WHEN** an admin launches one dataset at Minimal
- **THEN** that row’s Minimal cell shows generated · oracle · Δ and is clickable

#### Scenario: Compare shows two grids
- **WHEN** an admin opens `/admin/bench/tight/halles/minimal` after a run
- **THEN** the page shows generated planning then oracle planning, each with notes

### Requirement: Admin menu and Model / Manual / Delta
`/admin`, `/admin/bench`, and the compare page SHALL share a flat menu **Historique des computes | Banc** (current entry marked; no isolated « Banc » or « ← Admin » buttons). `/admin` remains the generate log. `/admin/bench` SHALL list datasets from the API (seven rows including three `crafted`). Each effort SHALL have three sub-columns **Modèle** / **Manuel** / **Delta** (`score.global` / `expected_score.global` / `deltas.global`, dash if no run); a click opens compare. Compare SHALL title `category · id · effort` and show **Modèle** then **Manuel** (notes + read-only grids).

#### Scenario: Admin menu has two entries
- **WHEN** an admin opens `/admin`
- **THEN** the page shows Historique des computes (marked) and Banc

#### Scenario: Bench table has seven rows and sub-columns
- **WHEN** an admin opens `/admin/bench`
- **THEN** the table has seven dataset rows including crafted atelier, rivoli, marais, and each effort has Modèle / Manuel / Delta headers

#### Scenario: Compare labels Model then Manual
- **WHEN** an admin opens a compare page
- **THEN** the two blocks are titled Modèle then Manuel

### Requirement: Score facts dictionary and clickable notes
The client SHALL parse cycle `facts[]` (`axis`, `kind`, `polarity`, `payload`) and recap cells `{ ok, kind, payload }`. `score` SHALL be notes + weights + global ; a leftover `resumes` key MUST be ignored (not required, not crashed). `/planning` and `/exemple` score pills SHALL be clickable and open one list: misses of that axis then hits (Globale = every fact including `role_gap`). Unknown `kind` SHALL render `kind` plus raw payload without inventing French. Pill subtitles SHALL be composed in the UI from `stats` and recap counts (not `score.resumes`). The alert list under the grid SHALL be evaluate misses only (`polarity == miss` and `kind != role_gap`). Legal / wish tables SHALL render from payload (Diane contrat `30h · 29h / 39h`). Sandbox overlay impact lists SHALL use the same dictionary ; `contract` / `role_fit` stay unchanged. Admin hover and planning JSON export SHALL use `facts` ; a legacy log item with `message` and empty payload SHALL show `message`. Bench compare MUST prefer `facts` and MUST NOT crash on legacy `warnings`.

#### Scenario: Example has 17 dictionary alerts
- **WHEN** `/exemple` loads Saint-Cloud
- **THEN** the alert list has 17 evaluate misses rendered via the dictionary, notes /10 remain, Diane contrat shows `30h · 29h / 39h`, and Théo Monday A midday is 11h–16h

#### Scenario: Click Occupation then Globale
- **WHEN** the restaurateur clicks Occupation then Globale on `/exemple` or `/planning`
- **THEN** each opens one list with that axis’s misses then hits (Globale includes `role_gap`)

#### Scenario: Effort switch uses that slot’s facts
- **WHEN** salle has both `versions.minimal` and `versions.optimized`
- **THEN** switching effort shows that slot’s facts without POSTing

### Requirement: Score pill title then note and gauge
`CycleScoreNotes` SHALL use the same layout on `/planning`, `/exemple`, and bench compare: title first, then note and gauge on the **same line** (fill `note / 10`, hue `12 × note`, `null` → empty gauge), then totaux on the next line (Globale has no totaux). Click SHALL list misses then hits. Globale remains first with a contrasted frame.

#### Scenario: Pill stacks title then note+gauge
- **WHEN** a pastille is rendered
- **THEN** the title sits above a row that aligns the numeric note with the gauge, and totaux (if any) sit under that row

### Requirement: Admin bench pack export
Compare SHALL parse `employees`, `model`, and `manual` (`CycleSlice`) and render both blocks with the same `CycleScoreNotes` (complete facts, stats, recap rows, real employee names). `/admin/bench` SHALL offer **Exporter sous le Manuel** (`GET /v1/admin/bench/export?scope=below_manuel`) and each table row plus the compare page SHALL offer **Exporter ce jeu** (`scope=dataset`). The browser SHALL download JSON named `bench-{category}-{id}.json` or `bench-below-manuel.json`.

#### Scenario: Compare uses full slices
- **WHEN** an admin opens compare after a run
- **THEN** Modèle and Manuel each show clickable notes with miss and hit facts, and grid names come from `employees` not ids

#### Scenario: Export dataset downloads a pack
- **WHEN** an admin clicks Exporter ce jeu on compare or a table row that has a run
- **THEN** the client GETs `scope=dataset` and downloads JSON with `kind: bench-pack`

### Requirement: Score tables Contrat legal wellbeing
The contrat pill SHALL be labeled **Contrat /10**. Axis titles SHALL be bold. Contrat totaux SHALL read `{h} occupées / {h}` without the word contrat, and `{ok}/{n} indispos respectées` when an indispo column exists. Pill click and the Alertes list SHALL share one 4-column table (Catégorie | Sous-catégorie | Statut ⚠️/✅ | Détail): all misses grouped by axis order, then all hits grouped the same way. `h2` SHALL have no subtitle. After Alertes on `/planning` and `/exemple`, the client SHALL render **Légal & Contrat** (`legal_cols` then Contrat then Indispos) then **Bien-être** (`wish_cols` minus contrat/indispo, omitted if empty). Recap cells SHALL be emoji plus measure without OK/Non tenu prefixes. Diane Saint-Cloud contrat SHALL show `⚠️ 30h · 29h / 39h`. Wizard copy stays. Bench compare SHALL keep pills and the 4-col click only.

#### Scenario: Example Contrat pill and fused tables
- **WHEN** `/exemple` loads Saint-Cloud
- **THEN** a Contrat /10 pill is present, Alertes is a 4-column table of evaluate misses, Légal & Contrat includes Diane `⚠️ 30h · 29h / 39h`, and Bien-être has no contrat/indispo columns

#### Scenario: Pill click lists misses then hits
- **WHEN** the restaurateur clicks Contrat then Globale
- **THEN** each opens the 4-column table with that axis’s (or all) misses grouped first, then hits

### Requirement: Admin bench table all engine versions
`/admin`, `/admin/bench`, the path compare, and `/admin/bench/run/{run_id}` SHALL share a flat menu **Historique des computes | Banc** (current entry marked; no Versions entry). `/admin/bench/versions` SHALL redirect to `/admin/bench`. `/admin/bench` SHALL GET `/v1/admin/bench/versions` and render one table: for each of Minimal, Optimisé, Maximal, sub-columns **Manuel** then each `engine_refs` value. Manuel SHALL show `dataset.manual.global` (dash if null) and a click SHALL open the path compare for that effort. An engine cell SHALL show that ref’s globale plus delta vs Manuel (dash if null); a click SHALL open `/admin/bench/run/{run_id}`. After a launch the page SHALL reload `/versions`. Subtitle remains `moteur {engine_ref}` for the current VERSION. Launch, export, run compare, and path compare stay unchanged. There SHALL be no revert button.

#### Scenario: Admin menu has two entries
- **WHEN** an admin opens `/admin`
- **THEN** the page shows Historique des computes (marked) and Banc, and no Versions entry

#### Scenario: Bench table has Manuel and engine_ref under each effort
- **WHEN** an admin opens `/admin/bench` after a Maximal run
- **THEN** each of the three computes has a Manuel column and a `core-0` column, and a click on `core-0` Maximal opens that run’s Modèle / Manuel compare

#### Scenario: Versions URL redirects to Banc
- **WHEN** an admin opens `/admin/bench/versions`
- **THEN** the client navigates to `/admin/bench`

### Requirement: Admin bench lists all API datasets
`/admin/bench` SHALL render one table row per dataset from `GET /v1/admin/bench/versions` (API order) and SHALL NOT hardcode a 7-dataset or 4-category catalogue. The launch toolbar SHALL include one row per distinct category in that list (`hours`, `size`, `overqual`, `closed`, `shapes`, and the older ones). Compare, export, and the three-effort × engine_ref columns stay unchanged.

#### Scenario: Thirty rows and new categories
- **WHEN** an admin opens `/admin/bench`
- **THEN** the table has 30 dataset rows and the launch bar shows hours, size, overqual, closed, and shapes

#### Scenario: Launch shapes category
- **WHEN** an admin launches category `shapes` at Minimal
- **THEN** the page does not crash and stays on `/admin/bench`

### Requirement: Admin bench lists fifty API datasets
`/admin/bench` SHALL render one table row per dataset from `GET /v1/admin/bench/versions` (API order) and SHALL NOT hardcode a 30-dataset, 7-dataset, or 6-crafted catalogue. The list SHALL include 50 datasets of which 26 are `crafted`. Launch, compare, export, and the three-effort × engine_ref columns stay unchanged. The UI SHALL NOT show worker chrome.

#### Scenario: Fifty rows including twenty-six crafted
- **WHEN** an admin opens `/admin/bench`
- **THEN** the table has 50 dataset rows and 26 of them have category `crafted`

#### Scenario: Launch crafted Maximal enqueues
- **WHEN** an admin launches category `crafted` at Maximal
- **THEN** the page stays on `/admin/bench` without crashing while the jobs enqueue

### Requirement: Admin bench table grouped by engine model
`/admin/bench` SHALL render one Manuel column at the left of the score cells (`dataset.manual.global`, dash if null). A click on Manuel SHALL open the path compare for `optimized` of the current engine. Each `engine_refs` value SHALL then be a family of three compute columns (Minimal, Optimisé, Maximal). An engine×compute cell SHALL show only the delta vs Manuel (dash if no run) and SHALL color it: green when the delta is 0, a red crescendo when negative (clamped at −1), a blue crescendo when positive (clamped at +1). A click SHALL open `/admin/bench/run/{run_id}`. Launch, export, and the 50-row list stay unchanged. The subtitle SHALL show the current VERSION `engine_ref`.

#### Scenario: One Manuel then families of three computes
- **WHEN** an admin opens `/admin/bench`
- **THEN** the table has a single Manuel column and each engine_ref has Minimal, Optimisé, and Maximal subcolumns

#### Scenario: Delta cells are colored
- **WHEN** an engine cell has a delta of 0, a negative delta, or a positive delta
- **THEN** the cell background is green, red-scaled, or blue-scaled respectively, and the label is the delta only

### Requirement: Admin bench recap and two-line launch
`/admin/bench` SHALL show a recap band after Launch and before the score table, one block per `engine_refs` value except the first, titled `{ref} vs {previous}`. Each block SHALL show, for Minimal / Optimisé / Maximal, a percent `100 × mean(global − prev.global) / 10`, plus max and min, over datasets where both globals are present. Empty intersection SHALL be a dash. Recap stat colors SHALL use the same delta rules as table cells. Launch SHALL have exactly two toolbar rows: all-categories × three efforts, and three effort dropdowns listing API categories; opening a dropdown SHALL NOT launch; choosing a category SHALL POST `scope=category` for that effort. There SHALL be no per-category launch row. The score table, export, and 50 rows stay unchanged.

#### Scenario: Recap compares consecutive engine_refs
- **WHEN** versions lists `core-2` then `core-3` and both have Maximal globals on the same datasets
- **THEN** a `core-3 vs core-2` block shows percent / max / min for Maximal

#### Scenario: Launch has two rows and category dropdowns
- **WHEN** an admin opens `/admin/bench`
- **THEN** Launch has two rows, no per-category row, and opening Maximal then choosing `crafted` enqueues that category

### Requirement: Admin bench gaps loader and bank export
`/admin/bench` SHALL include **Compléter les trous**, which POSTs `scope=gaps`. Leaving the page SHALL be safe. When a batch is active (`GET /v1/admin/bench/batches/active` on mount, or `batch_id` from a 202 lot / gaps launch), an overlay SHALL show `pct` and remaining `eta_max_seconds` formatted as `~ {duration}`, polling about every 2 seconds until `pct` is 100, then reload `/versions`. **Exporter tout le banc** SHALL GET `scope=bank` and download `bench-bank.json`. Recap, the two launch rows, and the score table stay otherwise unchanged.

#### Scenario: Gaps overlay shows percent and eta
- **WHEN** an admin clicks Compléter les trous and jobs are queued
- **THEN** the overlay shows a percent and a max remaining time, and the page stays on `/admin/bench`

#### Scenario: Bank export downloads
- **WHEN** an admin clicks Exporter tout le banc
- **THEN** the browser downloads `bench-bank.json`

### Requirement: Admin bench loader is inline under Launch
`/admin/bench` SHALL show batch `%` and remaining `eta_max_seconds` (`~ {duration}`) in the Launch section, immediately under the `h2`. The page SHALL NOT use `calc-overlay` or a page-wide blur/veil on `/admin/bench`. Table cells, recap, and export controls SHALL remain usable while a batch is active. Company `/planning` calc overlay SHALL stay unchanged. Polling `GET /v1/admin/bench/batches/active`, `batch_id` watch, and `scope=gaps` stay as in the previous requirement.

#### Scenario: Inline loader without veil
- **WHEN** an admin has an active bench batch on `/admin/bench`
- **THEN** percent and max remaining time appear under Launch, the page has no white overlay, and recap / table / export stay clickable

### Requirement: Admin bench stacked computes per model
`/admin/bench` SHALL use a single header row: one column per `engine_refs` value, with no `colSpan` and no second header row of Minimal | Optimisé | Maximal. Each model cell SHALL stack three deltas vertically in that order, each with a small effort label; a click SHALL open `/admin/bench/run/{run_id}`. Per-dataset Launch SHALL be a vertical `.bench-launch` stack (Minimal, Optimisé, Maximal) with Exporter ce jeu below. The global Launch toolbar rows SHALL stay horizontal. Manuel, recap, loader, gaps, export, and launch `locked = busy || exporting` stay unchanged.

#### Scenario: One column per engine_ref with three stacked deltas
- **WHEN** an admin opens `/admin/bench`
- **THEN** `core-3` is a single column whose cell shows Minimal, Optimisé, and Maximal deltas stacked, aligned with the row Launch buttons

### Requirement: Service types canonical order, Départ label, and time dial
Services types sub-tabs and typical-week columns SHALL list offered services as `CONTEXT_SERVICES.filter(s => offered.includes(s.id))` (Petit-déjeuner → Déjeuner → Dîner). The client MUST NOT derive that order from `services.map`. Persist `services[]` MUST remain the saved click/PATCH order. The type-sheet Type cell and thead SHALL say **Départ** (not Sortie) and **après départ**; JSON `departures` MUST stay unchanged. Adding an arrival or a departure SHALL open a time-dial dialog (`overlay-backdrop` + `overlay`, MUST NOT use `prompt()`) **before** inserting the row, prefilled 11h00 (arrival) or 16h00 (departure). Annuler, Escape, or a backdrop click MUST insert no row. Clicking the displayed stepper clock SHALL open the same dial to edit the current value; cancel SHALL leave the row unchanged. The dial SHALL offer hour buttons `0`…`23` **or** an integer 0–23, and minute buttons `00` / `15` / `30` / `45` **or** an integer 0–59; Valider MUST be disabled while either field is invalid. Persisted `time_minutes` SHALL be `hour * 60 + minutes` in 0…1439; if the edited row already had `time_minutes >= 1440`, the client SHALL keep `floor(old / 1440) * 1440` and add the dial value (MUST NOT fold end-of-service midnight back to 00h morning). The ±15 time stepper SHALL remain with no ceiling. When a time change (±15 or dial) changes chronological line order, the client SHALL animate the move for **≥ 500 ms** (visible, not a snap) and keep a focus background on the edited row until another time is edited. `prefers-reduced-motion` MAY snap the move but MUST still apply focus. React keys SHALL be `a-${index}` / `d-${index}` from the draft, not the sorted position. Level ± MUST NOT animate. The client MUST NOT add an npm dependency. `/exemple` `SERVICE_ROWS` and the sandbox overlay are out of this requirement.

#### Scenario: Offered services persisted déjeuner-first still display PDJ then déj then dîner
- **WHEN** the company has morning, midday, and evening offered with persist order midday first
- **THEN** Services types sub-tabs and typical-week columns are Petit-déjeuner, Déjeuner, Dîner

#### Scenario: Type sheet says Départ
- **WHEN** the restaurateur opens a type sheet that has a departure row
- **THEN** the Type cell and thead say Départ / après départ, not Sortie

#### Scenario: Add arrival through the dial at 8h07
- **WHEN** the restaurateur clicks Ajouter une arrivée, sets 8 and 07 on the dial, and validates
- **THEN** a new arrival row is inserted at 8h07

#### Scenario: Escape on add dial inserts nothing
- **WHEN** the restaurateur clicks Ajouter une arrivée then presses Escape (or Annuler / backdrop)
- **THEN** no new row is inserted

#### Scenario: Crossing times animates and keeps focus
- **WHEN** a ±15 (or dial) time change reorders two chrono lines
- **THEN** the edited row slides for at least 500 ms and keeps a focus background until another time is edited

### Requirement: Delete employee keep account
Équipe SHALL offer a trash control per fiche using the same chrome as roles. Confirm copy SHALL be French and SHALL name the fiche, list its unavailabilities and wishes, include *« Son accès à ce restaurant sera retiré. Il pourra se reconnecter avec le code entreprise. »* when that fiche has an account, and always include *« Le planning publié de la {salle|cuisine} sera retiré. L’autre équipe est inchangée. »*. A row that has never been PATCH’d MUST be dropped locally with no HTTP. A persisted fiche MUST `DELETE /v1/staff/{id}` with Bearer then `GET /v1/context` (MUST NOT omit a linked fiche via PATCH). `parseMe` MUST type `restaurant_id` as `string | null`. When `me.kind === "employee"` and `employee_id === null`, the client MUST NOT route to the employee grid at `/planning`; it SHALL show a company-code screen, `GET /v1/invites/{code}` for unlinked fiches, then `POST /v1/auth/link` `{ company_code, employee_id }` with Bearer. A 200 affiliated `me` SHALL go to `/planning`. The session chrome MUST omit « Planning » until affiliated. `/exemple` MUST stay unchanged.

#### Scenario: Trash on a persisted salle fiche
- **WHEN** the restaurateur confirms delete on a persisted salle fiche
- **THEN** the client DELETEs `/v1/staff/{id}`, GETs context, the fiche is gone, and the confirm mentioned the salle published planning (not cuisine)

#### Scenario: Trash on a local unsaved fiche
- **WHEN** the restaurateur adds a salarié then deletes that row before Enregistrer
- **THEN** the row disappears and the client MUST NOT call DELETE or PATCH

#### Scenario: Unaffiliated employee relinks
- **WHEN** a salarié with `employee_id` null enters a company code, picks an unlinked fiche, and submits
- **THEN** the client POSTs `/v1/auth/link` and on 200 opens `/planning`

### Requirement: Manual planning slot
Company `/planning` row 2 SHALL offer **Minimal | Optimisé | Maximal | Manuel**. Selecting **Manuel** MUST NOT POST generate and MUST hide **(Re)Calculer le planning**. When `ctx.ready[team]` is true the client SHALL show **Entrer en mode édition** even if `versions.manuel` is null. An empty Manuel slot while not editing SHALL show « Pas encore publié » (MUST NOT show « Pas encore calculé »). Enter SHALL `POST /v1/live/sandbox/{team}/enter` with `{ search_effort: "manuel" }` and SHALL reuse the live Overlay, FillOverlay, undo, discard, and publish. Compute slots SHALL stay unchanged (Recalculer + edit only if that cycle exists). The cycles parser SHALL accept a fourth `manuel` key ; if the key is missing it SHALL treat the slot as null. Cycle `search_effort` / `latest` MAY be `"manuel"`. `postGenerate` MUST NOT be called with `"manuel"`. `BENCH_EFFORTS` MUST remain `["minimal","optimized","maximal"]` and bench parsers MUST reject `"manuel"` as a search effort. `/exemple` MUST stay on `/v1/sandbox/*`. Overlay chrome for a computed edition MUST stay unchanged. A published Manuel timestamp SHALL show `generated_at` in `Europe/Paris`, MUST NOT append ` · engine_ref`, and SHALL show duration as an em dash when `duration_seconds` is absent. Version bar SHALL be `0.55.0` with note `Planning manuel`.

#### Scenario: Four selection crans
- **WHEN** a company session opens `/planning`
- **THEN** row 2 shows Minimal, Optimisé, Maximal, and Manuel

#### Scenario: Manuel hides Recalculer and offers edit when ready
- **WHEN** salle is ready, Manuel is selected, and `versions.manuel` is null
- **THEN** (Re)Calculer is absent, the empty copy is « Pas encore publié », and **Entrer en mode édition** is shown

#### Scenario: Enter manuel posts the slot key
- **WHEN** the restaurateur clicks Entrer en mode édition on Manuel
- **THEN** the client POSTs `/v1/live/sandbox/{team}/enter` with `{ search_effort: "manuel" }` and MUST NOT call `postGenerate`

#### Scenario: Cycles payload without manuel key
- **WHEN** GET `/v1/cycles` returns three version keys and no `manuel`
- **THEN** the client treats `versions.manuel` as null and still renders the Manuel cran

#### Scenario: Bench still has three efforts
- **WHEN** an admin opens `/admin/bench`
- **THEN** launch and parsers use only minimal, optimized, and maximal (`manuel` as a bench `search_effort` is rejected)

### Requirement: Admin historique note, view planning, impersonate link
`/admin` SHALL keep day headers, hover facts, and the engine selector. The generate table SHALL add **Note** after Effort (`formatCycleNote(score_global)`, one FR decimal or `—`) and **Planning** last (button **Voir**, disabled when `restaurant_id` is null). Column order SHALL be Heure, Email, Restaurant, Équipe, Effort, Note, Durée, Moteur, Warnings, Planning. `parseEntry` SHALL type `restaurant_id: string | null` and `score_global: number | null` (finite number or null); missing keys SHALL be null and MUST NOT throw. Right-click on **email** SHALL `preventDefault`. If `restaurant_id` is null the client SHALL toast `Restaurant introuvable.` and MUST NOT POST. Otherwise it SHALL `POST /v1/admin/impersonate` `{ restaurant_id }` with Bearer, copy `url` via `navigator.clipboard.writeText` (fallback allowed), and toast `Lien copié — ouvre-le en navigation privée.` The client MUST NOT `window.open` or auto-navigate to that url. Click **Voir** SHALL `go("/admin/planning/" + restaurant_id)`. `/admin/planning/{restaurant_id}` SHALL require `me.admin` (else the reserved message and zero fetch). It SHALL `GET /v1/admin/restaurants/{id}/cycles` and `/context`, reuse **PublishedPlanning** read-only (four slots, recaps, optional client export) and MUST NOT show (Re)Calculer, MUST NOT enter live sandbox, and MUST NOT show overlays. Title SHALL be the restaurant name. Admin nav SHALL stay Historique | Banc | Stats. 404 SHALL show `Restaurant introuvable.` (or API `detail`). `/impersonate/{token}` SHALL work without `me.admin` and when `me` is null (MUST NOT fall through to Login before consume). It SHALL `POST /v1/auth/impersonate` `{ token }` without Bearer. On 200 it SHALL store the session token (`AUTH_TOKEN_KEY`) and `go("/planning")`. On error it SHALL show `detail` and MUST NOT silently log the visitor in. Version bar SHALL be `0.56.0` with note `Note, voir le planning, lien de connexion`. File 71/72 (import popup, bench column chrome, … menu, Tous|IA|Manuels) MUST stay out of this slice.

#### Scenario: Admin table shows Note and Voir
- **WHEN** an admin opens `/admin` and a generate row has `score_global` 8.4 and a `restaurant_id`
- **THEN** Note shows `8,4` and Planning has an enabled **Voir** button

#### Scenario: Missing Infra keys do not crash
- **WHEN** GET `/v1/admin/generates` omits `restaurant_id` and `score_global`
- **THEN** the parser treats both as null, Note is `—`, **Voir** is disabled, and the page still renders

#### Scenario: Right-click email copies impersonate url
- **WHEN** an admin right-clicks an email whose row has `restaurant_id`
- **THEN** the client POSTs `/v1/admin/impersonate`, copies `url`, toasts `Lien copié — ouvre-le en navigation privée.`, and MUST NOT open a window

#### Scenario: Voir opens admin planning read-only
- **WHEN** an admin clicks **Voir**
- **THEN** the client goes to `/admin/planning/{restaurant_id}`, loads admin cycles + context, shows four slots and recaps, and does not offer (Re)Calculer or live edit

#### Scenario: Impersonate consume without session
- **WHEN** an anonymous visitor opens `/impersonate/{token}` and POST consume returns 200
- **THEN** the client stores the session token and goes to `/planning` without showing Login first

#### Scenario: Impersonate failure shows detail
- **WHEN** consume returns 401 `Lien expiré ou déjà utilisé.`
- **THEN** that `detail` is shown and the visitor is not sent to login as someone else

