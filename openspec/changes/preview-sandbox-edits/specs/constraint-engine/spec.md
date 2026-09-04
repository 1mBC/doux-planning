## ADDED Requirements

### Requirement: Retune hours of an existing shift
The engine SHALL preview new start and/or end times for one existing assignment without changing who holds it, which day it is on, or which service it belongs to. Candidates MUST sit on the 15-minute grid. Start times MUST lie within ±2 hours of the current start, and end times within ±2 hours of the current end, clipped to minutes 0 through 1440 (midnight as 1440, same convention as existing shifts). Each candidate duration MUST be at least that employee’s `min_shift_hours`. The current start–end pair MUST NOT appear as a candidate. Each candidate MUST be scored with the same evaluate path as any other draft. Proposal order MUST be the existing candidate ranking: fewest interdit warnings, then fewest souhait warnings, then earlier start, then earlier end. Each proposal MUST include rank, the new start and end, the engine warnings for that trial, and the warning delta versus the current draft.

#### Scenario: Fifteen-minute retune stays on the same person and service
- **WHEN** a sandbox shift is 11:00–16:00 for Théo on Monday midday and the restaurateur previews a retune
- **THEN** every proposal still assigns Théo on that Monday midday, times are multiples of 15 minutes, none equal 11:00–16:00, and none last fewer than Théo’s minimum shift

#### Scenario: Retune below the minimum is omitted
- **WHEN** a four-hour minimum employee holds 12:00–16:00 and a trial would last 3 hours 45 minutes
- **THEN** that trial is not in the preview list

### Requirement: Rank replacements on an occupied window
When the restaurateur asks who else can take an occupied slot, the engine MUST remove the current holder from that window only, then rank remaining eligible staff on that same window with the existing empty-slot candidate ranking (hard constraints first, then wellbeing cost, then existing tie-breaks). The current holder MUST NOT appear in that list. People already overlapping the window on another shift remain ineligible, as they are for an empty slot. Empty-slot ranking without a holder MUST stay unchanged.

#### Scenario: Occupied slot ranks others, not the holder
- **WHEN** Diane holds Monday midday 11:00–15:00 and the restaurateur previews a replacement on that slot
- **THEN** Diane is absent from the ranked list, other eligible salle staff are ordered as they would be for that empty window, and each proposal includes warnings and a delta versus the current draft

#### Scenario: Empty-slot ranking still skips occupants
- **WHEN** the restaurateur ranks candidates for a genuinely empty slot that overlaps an existing assignment
- **THEN** the person on that overlapping assignment is still omitted, as today

### Requirement: Preview swap partners for one occupied shift
When the restaurateur previews a swap from one assignment, the engine MUST evaluate swapping that assignment with each other assignment in the sandbox draft that belongs to a different person, using the existing two-person swap scoring. Proposal order MUST be the existing candidate ranking: fewest interdit warnings, then fewest souhait warnings, then a stable tie-break on the partner assignment. Each proposal MUST include rank, the partner (person, day, service, times), the engine warnings for that swapped draft, and the warning delta versus the current draft. Applying a swap MUST be the same dual reassignment as today’s single-pair swap.

#### Scenario: Swap preview lists other people’s shifts
- **WHEN** the restaurateur previews a swap from Théo’s Monday midday shift in a draft that also has Emma’s Wednesday evening and Diane’s Monday evening
- **THEN** Emma’s Wednesday evening and Diane’s Monday evening appear as partners, Théo’s own other shifts do not, and each partner is scored as a full two-person swap

### Requirement: Warning delta compares identity, not rewritten text
A preview proposal’s warning delta MUST classify each engine warning as added, removed, or unchanged relative to the current sandbox draft. Identity MUST be severity, code, employee, and day index — not the message text. Messages on the proposal MUST be the engine’s own messages for that trial. The system MUST NOT invent a second diagnostic sentence for the overlay.

#### Scenario: Same contract-hours warning stays unchanged
- **WHEN** the current draft already has a souhait `contract_hours` warning for Diane on week A and a retune trial still emits `contract_hours` for Diane on week A with a different hour count in the message
- **THEN** that warning is unchanged in the delta, and the proposal still shows the trial’s engine message

#### Scenario: New interdit is added
- **WHEN** a trial introduces an interdit rest warning that the current draft does not have
- **THEN** the delta lists that warning as added and does not list it as unchanged
