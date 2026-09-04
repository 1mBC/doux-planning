## Purpose

Lets the restaurateur open a French read-only web screen that shows the engine’s Saint-Cloud example snapshot: 14-day paper grid, warnings, stats, legal rows, and wish rows — without scoring, generating, or deciding in the client.

## ADDED Requirements

### Requirement: Client loads only the example snapshot
The web client SHALL obtain restaurant, legal context, and planning data solely by calling `GET /v1/examples/saint-cloud`. It MUST NOT call any other HTTP route, MUST NOT embed a second copy of the snapshot as source of truth, and MUST NOT invoke the constraint engine.

#### Scenario: Successful load
- **WHEN** the restaurateur opens the app and the example route returns 200 with `example`, `legal`, `restaurant`, and `planning`
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

### Requirement: French restaurateur chrome, read-only
All product chrome (titles, section labels, loading and error copy, severity names) SHALL be French. The screen MUST be read-only: no edit, swap, generate, publish, or sandbox control in this change.

#### Scenario: First useful screen
- **WHEN** the restaurateur opens the app on a desktop-width viewport with a valid snapshot
- **THEN** they can read week A, week B, the warning list, stats, legal table, and wish table without performing any mutation
