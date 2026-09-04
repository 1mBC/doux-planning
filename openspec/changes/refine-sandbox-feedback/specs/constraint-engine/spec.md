## ADDED Requirements

### Requirement: Retune preview is a single timed trial
The engine SHALL preview a retune as exactly one trial of an existing assignment: new start and end supplied by the caller, same person, day, and service. Times MUST be on the 15-minute grid, clipped to minutes 0 through 1440, with duration at least that employee’s `min_shift_hours`. The trial MUST be scored with `evaluate`. The sandbox draft MUST NOT change. If the requested (clipped) start and end equal the current shift, the system MUST fail the preview (error or empty proposal list) and MUST NOT return a successful no-op proposal. A duration below the minimum or a non-grid time MUST fail the same way.

#### Scenario: Plus or minus fifteen minutes
- **WHEN** Théo holds Monday midday 11:00–16:00 and the restaurateur previews a retune to 11:15–16:00
- **THEN** the preview returns one proposal for Théo on that Monday midday at 11:15–16:00, and the sandbox assignments are unchanged

#### Scenario: Same hours are rejected
- **WHEN** the restaurateur previews a retune whose start and end equal the current shift
- **THEN** the preview does not return a successful identity proposal

### Requirement: Occupied replace and swap rank by delta, not cycle totals
When ranking occupied-slot replacements or swap partners, the engine MUST sort by, in order: count of **added** interdit warnings vs the current draft, then count of **added** souhait warnings, then the change in keep-best hours-miss (`_hours_miss` of the trial minus `_hours_miss` of the current draft), then the keep-best `_attempt_key` of the trial. Empty-slot `rank_candidates` ordering MUST NOT change.

#### Scenario: One new interdit ranks before interdit plus broken wish
- **WHEN** two replacement trials each add one interdit and only the second also adds a souhait
- **THEN** the first trial is ranked above the second, even if the second has fewer souhait warnings on the whole 14-day trial

### Requirement: Preview impact is local to the gesture
Each preview proposal MUST include an impact summary with only: newly added interdit warnings; newly added souhait warnings other than `contract_hours`; contract movement (closer, farther, or excess vs contractual weekly hours) for people in the gesture only (retune: the shift holder; replace: outgoing and incoming; swap: both people; fill: the candidate); `empty_post` warnings added or removed; and `role_fit` (0 or 1 row) from downrole points on the clicked slot. The summary MUST NOT list other employees’ unchanged contract rows, MUST NOT dump unchanged cycle warnings, and MUST NOT invent diagnostic text — warning messages stay the engine’s.

#### Scenario: Improved contract for A omits unchanged B
- **WHEN** a retune improves Théo’s hours toward contract and Emma’s hours vs contract do not change
- **THEN** the impact contract list includes Théo and does not include Emma

### Requirement: Role-fit impact is downrole points on the clicked slot
Preview impact MUST include `role_fit` as zero or one row `{ current_gap, trial_gap, kind }` where gap is `employee.level - post_level` on the **clicked** preview shift only (retune, replace, and swap; not the swap partner). `kind` MUST be `better` when the trial gap is smaller than the current gap, and `worse` when it is larger. The row MUST be omitted when the gaps are equal, when an occupant is missing, when the post does not change (typical retune), or on fill of an empty cell. The system MUST NOT invent French diagnostic text and MUST NOT change occupied ranking.

#### Scenario: Replacing L4 with L2 on a level-1 post is better
- **WHEN** a level-4 holder on a post of level 1 is replaced by a level-2 employee
- **THEN** `role_fit` is one row with `current_gap` 3, `trial_gap` 1, and `kind` `better`, and the sandbox draft is unchanged

#### Scenario: Replacing L2 with L4 on a level-1 post is worse
- **WHEN** a level-2 holder on a post of level 1 is replaced by a level-4 employee
- **THEN** `role_fit` is one row with `current_gap` 1, `trial_gap` 3, and `kind` `worse`

#### Scenario: Same level on the clicked post is omitted
- **WHEN** a replacement keeps the same employee level on that post, or a swap keeps the same level on the clicked post
- **THEN** `role_fit` is empty

#### Scenario: Swap that changes the clicked post gap reports one row
- **WHEN** a level-4 holder on a post of level 1 is swapped with a level-2 employee on a different post
- **THEN** `role_fit` is one row with `current_gap` 3, `trial_gap` 1, and `kind` `better`

### Requirement: Empty-cell fill previews candidates without mutating the draft
The engine SHALL preview filling an empty row cell with `preview_fill`: slot `employee_id` (the row), `day_index`, `weekday`, `service_id`, `team`, plus optional start and end. Omitted hours MUST use the matching structure span (first arrival through last departure). Explicit hours MUST be on the 15-minute grid, clipped to 0–1440, with duration at least the row person’s `min_shift_hours`. Every candidate trial MUST use `post_level` equal to the row person’s `role.level`. If the row already has an assignment on that day and service, the preview MUST fail as occupied. Each eligible candidate MUST be scored with one `evaluate` of the draft plus that shift. The sandbox draft MUST NOT change. Rank 1 MUST be the row person when they can hold the post; other candidates MUST exclude the row person and MUST be sorted with `occupied_sort_key`. Each proposal MUST have gesture `fill`, the candidate `employee_id`, the trial start and end, empty `role_fit`, and the same impact/score fields as other previews. `apply_proposal` and undo MUST still cranter and restore.

#### Scenario: Empty Emma Monday midday ranks Emma first
- **WHEN** Emma’s Monday midday cell is empty and the restaurateur previews a fill with omitted hours
- **THEN** the first proposal is Emma, remaining proposals are the other eligible people ordered by `occupied_sort_key`, start and end equal the structure span, `role_fit` is empty, and the sandbox assignments are unchanged

#### Scenario: Occupied cell is rejected
- **WHEN** Emma already has an assignment on that Monday midday
- **THEN** fill preview fails as occupied

#### Scenario: Fill apply then undo restores
- **WHEN** the restaurateur applies a fill proposal and then undoes
- **THEN** history cranters on apply and assignments match the pre-fill draft after undo

### Requirement: Planning score is the keep-best key
Each preview proposal MUST expose the existing generation keep-best key (`empty_post` count, interdit count, hours-miss, souhait count, below-role count, overqualification) for the current sandbox draft and for the trial. The system MUST NOT compute a second scoring formula.

#### Scenario: Before and after keys
- **WHEN** a preview trial is scored
- **THEN** the proposal includes the keep-best key of the current draft and of that trial
