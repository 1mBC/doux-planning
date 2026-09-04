## Purpose

Fournit un moteur unique qui génère un cycle, évalue un planning, classe des candidats et produit des warnings, en respectant postes, légal, contrat, indisponibilités et bien-être.

## ADDED Requirements

### Requirement: Exclusive posts with nearest-level descent
Coverage MUST be a set of exclusive posts at required levels. An employee is eligible for a post only if their level is greater than or equal to the post level. A person occupies exactly one post for their entire shift. The only holder of a high post MUST NOT be assigned to a lower post if that would leave the high post empty. On a single service, unmatched posts stay empty rather than counting a higher post toward a lower headcount. Generation ranking across the cycle (hours vs level) is a separate requirement.

#### Scenario: Second chef fills sous-chef
- **WHEN** needed posts are chef, sous-chef, two commis, one plongeur, and available people are two chefs, one sous-chef, one commis, and no plongeur
- **THEN** one chef fills chef, the other chef fills sous-chef, sous-chef fills a commis post, commis fills commis, and the plongeur post remains empty

#### Scenario: Sole chef stays chef
- **WHEN** only one level-4 employee is present and both a chef post and a plongeur post are unfilled
- **THEN** that employee is assigned to the chef post, not the plongeur post

### Requirement: Do not steal the last person who can open an earlier post
When filling a later-starting post, generation MUST NOT assign the only remaining employee who can cover an earlier still-empty post of the same service and day, if another eligible person can take the later post. An opening hole (e.g. 10:00 level-1) SHALL be preferred over putting that opener on a 12:00 level-2.

#### Scenario: Opener kept for 10:00
- **WHEN** a 10:00 level-1 post and a 12:00 level-2 post are open, only Aurore can legally start at 10:00, and Vlad can take the level-2 post
- **THEN** generation assigns Vlad to level-2 and Aurore to the 10:00 level-1 post

### Requirement: Empty posts stay empty
Unfilled posts SHALL remain empty in this version. The system MUST surface them as couverture warnings. Filling by extras is out of scope.

#### Scenario: Hole visible
- **WHEN** a plongeur post cannot be filled from staff
- **THEN** the planning shows an empty post and a couverture warning

### Requirement: One engine for generate, evaluate, suggest, and swap
Generation of a 14-day cycle, scoring of a given planning, ranking of candidates to fill a slot, and evaluation of a two-person slot swap MUST use the same constraint engine and the same warning model.

#### Scenario: Swap is dual reassignment
- **WHEN** the restaurateur asks to swap two people’s slots in the sandbox
- **THEN** the engine scores the result of removing each from their slot and placing each on the other’s slot, and returns the same warning classes as any other edit

#### Scenario: Add-person ranking
- **WHEN** the restaurateur asks who can take an empty slot
- **THEN** the engine lists eligible profiles ordered by opportunity (hard constraints first, then wellbeing cost) and shows warnings per candidate

### Requirement: Three warning severities with override
The engine SHALL classify issues as: interdit (legal rest/hours maxima, stated unavailability), couverture (unfilled posts or unmet remaining-level rules after a departure), or souhait (wellbeing preferences, over-qualification beyond nearest level as applicable). The restaurateur MUST be able to publish despite warnings after acknowledging them. No constraint is a hard UI block.

#### Scenario: Publish with legal warning
- **WHEN** a draft violates 11 hours rest between two working days and the restaurateur acknowledges the interdit warning and publishes
- **THEN** the planning is published and the warning remains visible on the published planning

### Requirement: Legal rules are default, displayed, and scored
The system SHALL include these legal rules by default, display them to the restaurateur, and score them as interdit: 11 hours rest between two working days; two rest days per week; at most 5 hours pause between two services on the same day; at most 11 hours work per day for cuisine; at most 11.5 hours work per day for salle; at most 48 hours work per week.

#### Scenario: Rules are visible before generation
- **WHEN** the restaurateur views restaurant configuration
- **THEN** the six legal rules above are displayed

### Requirement: Contract hours are scored
The engine SHALL take contractual weekly hours into account when generating and scoring. Missing or exceeding contractual hours MUST produce a warning (souhait unless a later change tightens this). Contractual hours are a generation target, not only a post-hoc warning: see hours-then-level ranking. Generation MUST NOT exceed an employee’s contractual hours while teammates still have unused hours.

#### Scenario: Under-scheduled part-timer
- **WHEN** an employee with 20 contractual hours is assigned 8 hours in a cycle week
- **THEN** the engine reports a warning on that employee’s hours

#### Scenario: Generation aims at contract hours
- **WHEN** two employees can fill the same post and one is already at contractual hours while the other is under
- **THEN** generation assigns the under-hours employee

### Requirement: Generation does not assign unavailable staff
When generating a cycle, the engine MUST NOT assign an employee to a slot that their restaurateur-stated unavailability blocks. An empty post (couverture warning) is preferred over placing an unavailable person. Manual override after generation MAY still place them and MUST then score an interdit warning.

#### Scenario: Weekday unavailability skipped
- **WHEN** an employee is unavailable every Monday and a Monday midday post needs filling
- **THEN** generation leaves that employee unassigned on Monday even if they are the highest level available

#### Scenario: Service unavailability skipped
- **WHEN** an employee is unavailable for weekday midday services
- **THEN** generation MAY assign them to weekday evening but MUST NOT assign them to weekday midday

### Requirement: Generation does not exceed contract while teammates are under
Generation MUST NOT assign a shift that would put an employee above their contractual weekly hours while any teammate on the same team is still under their contractual hours for that week. An empty post (couverture) is preferred over overloading the only person left on that slot. Manual override after generation MAY exceed hours and MUST then score a souhait warning.

#### Scenario: Part-timer stops at contract
- **WHEN** a 15-hour employee is already at 15 hours and a remaining post is open, and a 35-hour teammate is still under hours
- **THEN** generation does not assign that post to the 15-hour employee

### Requirement: Rest days leave enough people for coverage
When planning rest days, the engine SHALL keep enough eligible staff **reserved for each open service** (team, service, day) to cover that service’s posts. A person reserved for one service MUST NOT count toward another service’s coverage that day unless they are also reserved for it, and reservation MUST respect that employee’s daily and weekly hour caps (using the shortest post of each reserved service). The number of services an employee may be reserved for in a week MUST NOT exceed `floor(contractual hours / typical post duration)`, where typical duration is the median length of posts they are eligible for that week; if that floor is zero but the shortest eligible post still fits the contract, they MAY be reserved for one service. They MUST NOT be reserved on more open days than that shift budget. Days they cannot work at all (closed, forced off, or no eligible post) already count as rest. It MUST NOT rest an employee on a day where they are among the only people who can fill remaining posts, if another rest day in the week is possible. Closed days already count as rest.

#### Scenario: Opening post not left empty by rest pile-up
- **WHEN** a weekday midday needs four posts and exactly four employees are eligible for that midday (others unavailable)
- **THEN** generation does not rest any of those four that day, and the four posts are filled if hours and overlap allow

#### Scenario: Part-timer reserved for as many services as hours allow
- **WHEN** an employee has a 15-hour contract and the typical eligible post that week lasts five hours
- **THEN** generation reserves them for at most three services that week (and therefore at most three open days)

### Requirement: Consecutive rest is two weekdays, not the weekend
Two consecutive rest days SHALL be two adjacent weekdays (Monday–Tuesday, Tuesday–Wednesday, Wednesday–Thursday, or Thursday–Friday). Generation MUST NOT use Saturday–Sunday, Friday–Saturday, or Sunday–Monday to satisfy this preference. Weekend rest is a separate preference. A closed Sunday does not turn Saturday into the consecutive partner.

#### Scenario: Consecutive rest does not empty Saturday
- **WHEN** employees prefer two consecutive rest days and the restaurant is closed on Sunday
- **THEN** generation places those two days on weekdays and still staffs Saturday posts from that pool

### Requirement: Finish a day already started before opening another person
When several people are legally eligible for a post and their hours-to-contract ratios are equal, generation SHALL prefer an employee who already has a shift that day (and would stay within contract, legal maxima, and their weekly coupure cap) over someone who is still off that day. A second service that would exceed that employee’s weekly coupure cap MUST be skipped, the same way unavailability is skipped.

#### Scenario: Evening continues the midday person at equal load
- **WHEN** Aurore already has a midday shift, Lucie is free that day, both can legally take the evening post, both have the same hours-to-contract ratio, and the evening would not exceed Aurore’s coupure cap
- **THEN** generation assigns Aurore

### Requirement: Generation searches other arrangements when a greedy pass leaves a hole
Generation SHALL try several deterministic rest calendars that still cover each open service (no immediate coverage hole: enough people reserved per service, legal rest days, hour caps), fill each calendar, MAY reassign a same-day shift onto an empty post when another eligible colleague can take the vacated post, and SHALL keep the attempt with the fewest empty posts, then fewest interdit warnings, then closest contract hours, then fewest souhait, then fewest shifts below the person's role level. Search breadth is an input `search_effort`: **minimal** (16 covering calendars), **optimized** (default: 20× that bound, still seconds), **maximal** (every covering calendar, minutes acceptable). The same inputs and the same effort MUST produce the same generated planning. Random non-reproducible generation MUST NOT be used.

#### Scenario: Midday person is moved so evening can fill
- **WHEN** Monday has one midday post and one evening post, Alex can do either but only has hours for one, Blair can only do midday, and Casey can only do evening but is off Monday
- **THEN** generation assigns Blair to midday and Alex to evening, with no empty Monday post

### Requirement: Coupure count is per week
Wellbeing limits of at most two or three coupures SHALL be counted per calendar week of the cycle (week A and week B separately), not as a total over 14 days. A coupure is a same-day gap between two shifts. Generation MUST NOT assign a shift that would exceed that cap; an empty post or another eligible colleague is preferred. A hand-built or overridden draft that already exceeds the cap MUST still score a souhait warning. A legal pause longer than 5 hours remains an interdit.

#### Scenario: Three split days in week A only
- **WHEN** an employee prefers at most two coupures per week and a draft already has three midi+soir days in week A and two in week B
- **THEN** the engine reports a souhait max_coupures warning on week A and not on week B

#### Scenario: Generation stops at the weekly coupure cap
- **WHEN** an employee has a cap of two coupures per week, already has two midi+soir days this week, and an evening post would be a third coupure
- **THEN** generation does not assign that evening to them

### Requirement: Generation ranks by hours-to-contract, then nearest level
When generating, for each post the engine SHALL choose among eligible staff (right team, level ≥ post, not unavailable, not overlapping, not over legal maxima when another eligible person exists) in this order:

1. Lowest projected weekly hours-to-contract ratio after the assignment (hours already assigned this week plus this shift, divided by contractual hours).
2. Already working that day (complete a started day before opening a new person at the same ratio).
3. Nearest skill level (exact match before overqualification).

A higher level SHALL take a lower-level post as soon as closer-level eligible colleagues are more loaded on that ratio (including already at or above contract). Concretely: a level-4 SHALL fill a level-3 post when eligible level-3 staff are more loaded than that level-4; a level-4 SHALL fill a level-2 post when eligible level-2 and level-3 staff are more loaded; a level-3 SHALL fill a level-2 post when eligible level-2 staff are more loaded. The engine MUST NOT dump every post on the highest rank while a closer-level colleague still has a lower or equal hours-to-contract ratio.

#### Scenario: Equal hours, exact level wins
- **WHEN** a level-3 post is open and both a level-4 and a level-3 employee are eligible with the same hours-to-contract ratio
- **THEN** generation assigns the level-3 employee

#### Scenario: Level-4 absorbs an overloaded level-3
- **WHEN** a level-3 post is open, the eligible level-3 employee is already at or above contractual hours (or would be after this shift), and a level-4 colleague is still under hours
- **THEN** generation assigns the level-4 employee

#### Scenario: Level-3 absorbs an overloaded level-2
- **WHEN** a level-2 post is open, the eligible level-2 employee is already at or above contractual hours (or would be after this shift), and a level-3 colleague is still under hours
- **THEN** generation assigns the level-3 employee

### Requirement: Minimum shift length
Generation MUST NOT assign an employee to a post shorter than that employee’s `min_shift_hours` (default 4). That minimum is per employee, not a frozen global constant; a restaurateur MAY lower it on a profile. Posts are paired FIFO when remaining coverage still allows it (higher skill stays if the remaining posts need that skill). If the resulting window is still shorter than that employee’s minimum, generation MUST stretch the shift to that minimum (extend the end first, then the start) within the service span, even if that overstaffs the tail of the service. An empty post is used only when the service span cannot fit the minimum. Having already worked another service that day MUST NOT authorize a shorter shift.

#### Scenario: FIFO opener leaves first
- **WHEN** two level-1 posts start at 10:00 and 11:00 and one level-1 leaves at 14:00
- **THEN** generation treats the 10:00 post as 10:00–14:00 and the 11:00 post as 11:00–15:00

#### Scenario: Higher-skill opener stays until close
- **WHEN** a level-3 opener starts at 18:00 and remaining coverage at 22:30 still includes a level-3 post
- **THEN** that opener’s window runs until the last departure of the service

#### Scenario: Three-hour closer is stretched
- **WHEN** an employee has the default 4-hour minimum and a closer post is 19:30–22:30 while the service continues until 24:00
- **THEN** generation assigns 19:30–23:30 rather than leaving the post empty

#### Scenario: Service too short stays empty
- **WHEN** an employee has the default 4-hour minimum and the whole service is only 3 hours
- **THEN** generation leaves that post unassigned

### Requirement: Generate a full 14-day cycle
The engine MUST generate week A and week B as one problem, including wrap-around rest and every-other-weekend preferences. Sequential independent week solves MUST NOT be the generation method.

#### Scenario: Alternate weekends
- **WHEN** an employee prefers one weekend off every two weeks
- **THEN** a generated cycle that assigns both weekends worked, or neither weekend off, is scored with a souhait warning, and a valid generation prefers exactly one weekend off in the 14 days

### Requirement: Time coverage evaluated on 15-minute slices
The engine SHALL evaluate post coverage along the service structure using 15-minute slices derived from arrival and departure waves. Decision variables MAY be shift templates taken from those waves rather than one variable per slice.

#### Scenario: Coverage gap between waves
- **WHEN** a structure requires a level-4 post from 10:00 and the assigned chef shift starts at 11:00
- **THEN** the engine reports a couverture warning for 10:00–11:00
