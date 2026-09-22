# Spec Delta

## MODIFIED Requirements

### Requirement: Legal rules are default, displayed, and scored
The system SHALL include these legal rules by default, display them to the restaurateur, and score them as interdit: 11 hours rest between two **adjacent** working days (a rest day in between means the pair is not checked, including across the 14-day wrap); two rest days per week; at most 5 hours pause between two services on the same day; at most 11 hours work per day for cuisine; at most 11.5 hours work per day for salle; at most 48 hours work per week.

#### Scenario: Rules are visible before generation
- **WHEN** the restaurateur views restaurant configuration
- **THEN** the six legal rules above are displayed

#### Scenario: Sunday off between Saturday and Monday
- **WHEN** a person works Saturday until 24:00, has no Sunday shift, and starts Monday at 10:00
- **THEN** evaluate MUST NOT emit `rest_between_days` for that pair

#### Scenario: Adjacent wrap Sunday to Monday
- **WHEN** a person works Sunday 14:00–23:00 and Monday 08:00–16:00
- **THEN** evaluate emits `rest_between_days` interdit

### Requirement: Minimum shift length
Generation MUST NOT assign an employee to a post shorter than that employee’s minimum for the post’s service (`morning`, `midday`, or `evening`; default 4 when that key is absent). That minimum is per employee and per service, not a frozen global constant; a restaurateur MAY lower it on one service without changing the others. Posts are paired FIFO when remaining coverage still allows it (higher skill stays if the remaining posts need that skill). A post still live after the last departure wave MUST run until that last wave’s clock, never before the first departure, aligned with who remains in the bag. If the resulting window is still shorter than that service’s minimum, generation MUST stretch the shift to that minimum (extend the end first, then the start) within the service span, even if that overstaffs the tail of the service. An empty post is used only when the service span cannot fit the minimum. Having already worked another service that day MUST NOT authorize a shorter shift.

#### Scenario: FIFO opener leaves first
- **WHEN** two level-1 posts start at 10:00 and 11:00 and one level-1 leaves at 14:00
- **THEN** generation treats the 10:00 post as 10:00–14:00 and the 11:00 post as 11:00–15:00

#### Scenario: Higher-skill opener stays until close
- **WHEN** a level-3 opener starts at 18:00 and remaining coverage at 22:30 still includes a level-3 post
- **THEN** that opener’s window runs until the last departure of the service

#### Scenario: Leftover remaining bag is not a zero-length post
- **WHEN** the last MIDI departure at 16:00 still lists remaining `[3]` after a first departure at 15:30
- **THEN** the L3 post that arrived at 10:30 ends at 16:00, not at 10:30, and a 4-hour stretch MUST NOT invent a 14:30 leave

#### Scenario: Three-hour closer is stretched
- **WHEN** an employee has the default 4-hour minimum and a closer post is 19:30–22:30 while the service continues until 24:00
- **THEN** generation assigns 19:30–23:30 rather than leaving the post empty

#### Scenario: Service too short stays empty
- **WHEN** an employee has the default 4-hour minimum and the whole service is only 3 hours
- **THEN** generation leaves that post unassigned

### Requirement: Generate a full 14-day cycle
The engine MUST generate week A and week B as one problem, including wrap-around rest (only when the last and first worked days are adjacent) and at-least-one-weekend-off preferences. Sequential independent week solves MUST NOT be the generation method.

#### Scenario: Alternate weekends
- **WHEN** an employee prefers one weekend off every two weeks (`every_two`)
- **THEN** a generated cycle that assigns both weekends worked is scored with a souhait warning; a cycle with one or both weekends fully off holds the wish; generation MUST allow both weekends off (SAT `even_off + odd_off >= 1`)
