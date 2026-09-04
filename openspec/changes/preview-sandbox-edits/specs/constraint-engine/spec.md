## ADDED Requirements

### Requirement: Retune preview is a single timed trial
The engine SHALL preview a retune as exactly one trial of an existing assignment: new start and end supplied by the caller, same person, day, and service. Times MUST be on the 15-minute grid, clipped to minutes 0 through 1440, with duration at least that employee’s `min_shift_hours`. The trial MUST be scored with `evaluate`. The sandbox draft MUST NOT change. If the requested (clipped) start and end equal the current shift, the system MUST fail the preview (error or empty proposal list) and MUST NOT return a successful no-op proposal. A duration below the minimum or a non-grid time MUST fail the same way.

#### Scenario: Plus or minus fifteen minutes
- **WHEN** Théo holds Monday midday 11:00–16:00 and the restaurateur previews a retune to 11:15–16:00
- **THEN** the preview returns one proposal for Théo on that Monday midday at 11:15–16:00, and the sandbox assignments are unchanged

#### Scenario: Same hours are rejected
- **WHEN** the restaurateur previews a retune whose start and end equal the current shift
- **THEN** the preview does not return a successful identity proposal

### Requirement: Rank replacements on an occupied window
When the restaurateur asks who else can take an occupied slot, the engine MUST remove the current holder from that window only, then rank remaining eligible staff on that same window. Occupied replace and swap MUST sort by added interdit warnings vs the current draft, then added souhait warnings, then hours-miss change, then keep-best `_attempt_key`. The current holder MUST NOT appear in the replace list. Empty-slot `rank_candidates` ordering MUST NOT change.

#### Scenario: Occupied slot ranks others, not the holder
- **WHEN** Diane holds Monday midday 11:00–15:00 and the restaurateur previews a replacement on that slot
- **THEN** Diane is absent from the ranked list

#### Scenario: One new interdit ranks before interdit plus broken wish
- **WHEN** two replacement trials each add one interdit and only the second also adds a souhait
- **THEN** the first trial is ranked above the second

#### Scenario: Empty-slot ranking still skips occupants
- **WHEN** the restaurateur ranks candidates for a genuinely empty slot that overlaps an existing assignment
- **THEN** the person on that overlapping assignment is still omitted, as today

### Requirement: Preview swap partners for one occupied shift
When the restaurateur previews a swap from one assignment, the engine MUST evaluate swapping that assignment with each other assignment that belongs to a different person, using the existing two-person swap scoring, then sort with the occupied delta key plus a stable partner tie-break. Applying a swap MUST be the same dual reassignment as today’s single-pair swap.

#### Scenario: Swap preview lists other people’s shifts
- **WHEN** the restaurateur previews a swap from Théo’s Monday midday shift in a draft that also has Emma’s Wednesday evening and Diane’s Monday evening
- **THEN** Emma’s Wednesday evening and Diane’s Monday evening appear as partners, and Théo’s own other shifts do not

### Requirement: Preview impact is local to the gesture
Each preview proposal MUST include an impact summary with only: newly added interdit warnings; newly added souhait warnings other than `contract_hours`; contract movement (closer, farther, or excess vs contractual weekly hours) for people in the gesture only; `empty_post` warnings added or removed; and `role_fit` (0 or 1 row) from downrole points on the clicked slot. The summary MUST NOT list other employees’ unchanged contract rows, MUST NOT dump unchanged cycle warnings, and MUST NOT invent diagnostic text.

#### Scenario: Improved contract for A omits unchanged B
- **WHEN** a retune improves Théo’s hours toward contract and Emma’s hours vs contract do not change
- **THEN** the impact contract list includes Théo and does not include Emma

### Requirement: Role-fit impact is downrole points on the clicked slot
Preview impact MUST include `role_fit` as zero or one row `{ current_gap, trial_gap, kind }` where gap is `employee.level - post_level` on the clicked preview shift only (not the swap partner). `kind` MUST be `better` when the trial gap is smaller, `worse` when larger. The row MUST be omitted when gaps are equal, when an occupant is missing, when the post does not change, or on fill.

#### Scenario: Replacing L4 with L2 on a level-1 post is better
- **WHEN** a level-4 holder on a post of level 1 is replaced by a level-2 employee
- **THEN** `role_fit` is one row with `current_gap` 3, `trial_gap` 1, and `kind` `better`

#### Scenario: Swap that changes the clicked post gap reports one row
- **WHEN** a level-4 holder on a post of level 1 is swapped with a level-2 employee on a different post
- **THEN** `role_fit` is one row with `current_gap` 3, `trial_gap` 1, and `kind` `better`

### Requirement: Empty-cell fill previews candidates without mutating the draft
The engine SHALL preview filling an empty row cell with `preview_fill`. Omitted hours MUST use the matching structure span. `post_level` MUST equal the row person’s `role.level`. An existing assignment for that row × day × service MUST fail as occupied. Rank 1 MUST be the row person when they can hold the post; others MUST use `occupied_sort_key`. `role_fit` MUST be empty. `apply_proposal` and undo MUST still cranter and restore.

#### Scenario: Empty Emma Monday midday ranks Emma first
- **WHEN** Emma’s Monday midday cell is empty and the restaurateur previews a fill with omitted hours
- **THEN** the first proposal is Emma, start and end equal the structure span, `role_fit` is empty, and the sandbox assignments are unchanged

### Requirement: Planning score is the keep-best key
Each preview proposal MUST expose the existing generation keep-best key for the current sandbox draft and for the trial. The system MUST NOT compute a second scoring formula.

#### Scenario: Before and after keys
- **WHEN** a preview trial is scored
- **THEN** the proposal includes the keep-best key of the current draft and of that trial

### Requirement: Warning delta compares identity, not rewritten text
A preview proposal’s warning delta MUST classify each engine warning as added, removed, or unchanged relative to the current sandbox draft. Identity MUST be severity, code, employee, and day index — not the message text.

#### Scenario: Same contract-hours warning stays unchanged
- **WHEN** the current draft already has a souhait `contract_hours` warning for Diane on week A and a retune trial still emits `contract_hours` for Diane on week A with a different hour count in the message
- **THEN** that warning is unchanged in the delta

#### Scenario: New interdit is added
- **WHEN** a trial introduces an interdit rest warning that the current draft does not have
- **THEN** the delta lists that warning as added
