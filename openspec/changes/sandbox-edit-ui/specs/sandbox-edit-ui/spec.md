## Purpose

Lets the restaurateur open a French edit mode on top of the example screen: occupied-slot overlay, engine preview proposals, commit that replaces the draft grid, and last-cran undo — without scoring or generating in the client.

## ADDED Requirements

### Requirement: Edit mode loads the sandbox, not the example snapshot
The client SHALL enter edit mode only via `POST /v1/sandbox/enter`. After a successful enter, the grid and warnings MUST come from that sandbox state (and later `GET /v1/sandbox`, commit, undo, or discard bodies). The client MUST parse `score` from that body and MAY display it as-is (plus petit = mieux). The client MUST NOT use `GET /v1/examples/saint-cloud` as the source of edited shifts, and MUST NOT recompute `score`. Outside edit mode, the existing example screen SHALL remain available. Choosing **Lecture** MUST leave edit mode without calling discard.

#### Scenario: Enter edit mode
- **WHEN** the restaurateur clicks « Mode édition » and enter returns 200
- **THEN** the grid shows `planning.assignments` from that body and the warning list shows `planning.warnings` from that body

#### Scenario: Example screen still works
- **WHEN** the restaurateur has not entered edit mode
- **THEN** the client still loads the example snapshot on a single `GET /v1/examples/saint-cloud` as before

### Requirement: Occupied-slot overlay previews then commits a gesture
Clicking a filled start, end, or duration cell SHALL open an overlay. The restaurateur MUST choose `retune` (changer les heures), `replace` (attribuer une autre personne), or `swap` (échanger). The client MUST NOT show proposal `delta` or the full cycle `warnings` list. Choosing a proposal SHALL `POST /v1/sandbox/commit` with the gesture fields (retune: start/end ; replace: employee_id ; swap: partner) and MUST replace grid, warnings, score, and history from the 200 body.

#### Scenario: Occupied cell opens the three-gesture overlay
- **WHEN** the restaurateur clicks a filled start, end, or duration cell in edit mode
- **THEN** the overlay offers changer les heures, attribuer, and échanger

### Requirement: Empty-cell overlay fills via preview hours
In edit mode, clicking a rest cell SHALL open a fill overlay (not the three occupied gestures). The client SHALL `POST /v1/sandbox/preview` with `{ gesture: "fill", slot, start_minutes: null, end_minutes: null }`. `slot.weekday` MUST be `monday`…`sunday` from `day_index % 7`. `slot.team` MUST be the row person’s `team`. After 200, the stepper SHALL use `proposals[0].start_minutes` and `end_minutes` (MUST NOT invent hours). Each ±15 SHALL preview with both minutes after the step. The line person SHALL appear at the top with impact and **Valider** when present in `proposals`. Other proposals SHALL list below in `rank` order, titled by name, with the same impact as replace. Commit SHALL send `{ gesture: "fill", slot, employee_id, start_minutes, end_minutes }` using preview hours, never null. A 409 MUST show the French `detail`, keep the overlay open, and MUST NOT change the grid. History SHALL label the cran « Créneau posé ».

#### Scenario: Fill Emma Monday morning
- **WHEN** the restaurateur is in edit mode and clicks Emma’s empty Monday morning cell
- **THEN** the overlay previews fill, shows the structure span from `proposals[0]`, lists other people below, and does not hardcode 10h

#### Scenario: Fill 409 stays in the overlay
- **WHEN** fill preview or commit returns 409
- **THEN** the restaurateur sees the French `detail`, the overlay stays open, and the grid is unchanged

### Requirement: Retune overlay steps fifteen minutes then previews one trial
Choosing « Changer les heures » SHALL show one **début** row and one **fin** row, each with `−` / `+` (15 minutes). The client MUST NOT preview until a step. Each click SHALL `POST /v1/sandbox/preview` with `{ gesture: "retune", shift, start_minutes, end_minutes }` using the hours **after** the step. The client SHALL display the single returned proposal’s `impact` (`new_interdits` and `coverage_added` as new warnings in orange ; contract `closer` in green « gagné N min » from `(trial_hours - current_hours)` in minutes ; `farther` / `excess` in red ; `role_fit` as specified below). Unchanged contract rows MUST NOT be listed. An empty `role_fit` MUST NOT be listed. Contract lines SHALL append `(current% → trial%)` from `current_hours / contracted * 100` and `trial_hours / contracted * 100` (French decimal comma) unless `contracted` is 0. The client MUST parse `current_score` / `trial_score` and MUST NOT display them in the overlay. Commit uses a **Valider** control and SHALL send those start/end.

#### Scenario: Preview then commit retune
- **WHEN** the restaurateur opens a filled cell, chooses changer les heures, steps +15 on fin, sees one impact, and commits
- **THEN** the overlay used preview with the stepped start/end then commit with those minutes, the cell reflects the committed draft, and the client did not enumerate or rescore trials

#### Scenario: Identity retune stays in the overlay
- **WHEN** preview returns 400 because the hours match the current slot
- **THEN** the restaurateur sees the French `detail`, the draft is unchanged, and the overlay stays open

### Requirement: Replace and swap overlays list engine-ranked impact
Choosing replace or swap SHALL `POST /v1/sandbox/preview` with `{ gesture, shift }` (shift identity fields from the contract, without requiring `duration_hours`). The client SHALL list `proposals` in `rank` order. Replace row title is the person. Swap row title is **day then time** (`weekday` / `day_index` plus clock). Each row SHALL show only `impact` (interdits in red, broken wishes in orange, contract of both people in green when `kind` is `closer` and yellow otherwise, with the same contract % parentheses as retune, and `role_fit`). The client MUST NOT display `current_score` / `trial_score`, MUST NOT display `delta +/−/=`, and MUST NOT list the trial’s full cycle warnings.

#### Scenario: Preview then commit swap
- **WHEN** the restaurateur chooses échanger and commits a ranked proposal
- **THEN** the overlay listed proposals in engine rank order with the partner’s day before the clock, commit used that partner identity, and the client did not reorder or rescore

### Requirement: Role-fit impact uses API gaps only
The client SHALL parse `impact.role_fit` (0 or 1 object with `current_gap`, `trial_gap`, `kind`). A `better` row SHALL be green « poste plus proche du niveau (−N) » with `N = current_gap - trial_gap`. A `worse` row SHALL be red « surqualification +N » with `N = trial_gap - current_gap`. An empty list SHALL show no rôle line. The client MUST NOT recompute N from employee level or post level. « Aucun impact listé » MUST appear only when every impact list (including `role_fit`) is empty of shown rows.

#### Scenario: Replace a lower post with a closer level
- **WHEN** the restaurateur previews replace on a low post and a candidate returns `role_fit` `better`
- **THEN** that proposal shows a green poste-plus-proche line and the client did not invent the gap

#### Scenario: Same-level candidate
- **WHEN** preview replace returns `role_fit: []` for a candidate
- **THEN** that proposal has no rôle line

### Requirement: History undo is last-cran only
The client SHALL list `history` crans from the API recap (not a React journal): `gesture`, `shift` or `slot`, `employee_id`, `start_minutes`, `end_minutes`, `partner`, `impact`. The client MUST NOT require `current_score` on a cran. Display SHALL use a synthetic proposal for impact (dummy scores allowed because scores are not shown). `startEdit`, GET, commit, undo, and discard SHALL replace the list from that body. Undo SHALL call `POST /v1/sandbox/undo` and replace state from the 200. A 409 MUST show the API `detail` in French and MUST NOT change the draft. The client MUST NOT undo a cran in the middle of the pile. **Lecture** MAY drop local React state; re-entering edit MUST still show who / hours / impact from the recap.

#### Scenario: Undo restores the previous draft
- **WHEN** one cran is committed and the restaurateur undoes
- **THEN** assignments and warnings match the pre-commit sandbox state and `history` is empty

#### Scenario: Empty pile
- **WHEN** undo returns 409
- **THEN** the shown grid is unchanged and the restaurateur sees the French detail

#### Scenario: Recap survives Lecture
- **WHEN** the restaurateur commits a cran, clicks Lecture, then Mode édition
- **THEN** the history still shows who, hours, and impact from the API recap

### Requirement: Discard resets the draft
When `history.length > 0`, the client SHALL show **Tout annuler** and on click `POST /v1/sandbox/discard`. A 200 MUST replace the grid with the returned draft and show an empty history. A 404 MUST show the French `detail` and MUST NOT change the grid. **Lecture** MUST NOT call discard. The example snapshot (hours %) MUST remain unchanged.

#### Scenario: Tout annuler restores the hydrated cycle
- **WHEN** at least one cran is committed and the restaurateur clicks Tout annuler
- **THEN** the draft matches the initial sandbox (empty history) and the example screen still shows 92 %

#### Scenario: Discard without sandbox
- **WHEN** discard returns 404
- **THEN** the shown grid is unchanged and the restaurateur sees the French detail

### Requirement: No invented sandbox recap
While in edit mode the client MUST NOT invent `legal_rows`, `wish_rows`, or `stats` on the sandbox payload. Legal and wish tables from the last example MAY stay visible only as read-only example context, or be hidden; they MUST NOT be presented as the current draft.

#### Scenario: Sandbox body has no stats
- **WHEN** enter returns planning without `stats`
- **THEN** the edit screen does not display a Heures vs contrat / Souhaits bien-être recap computed from draft warnings
