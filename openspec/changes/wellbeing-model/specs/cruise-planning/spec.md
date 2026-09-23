## ADDED Requirements

### Requirement: Structured wellbeing and day-by-service unavailability
The system SHALL store wellbeing as consecutive rest, at most one weekend choice, optional per-service caps, and an optional coupure cap that may be zero. Unavailability MUST be an exact weekday and company service pair. Deleted wellbeing keys and every-morning / every-evening flags MUST be rejected. Week labels for the restaurant MUST be parity when any fiche asks for an even or odd weekend, otherwise A/B.

#### Scenario: Sunday closed consecutive rest
- **WHEN** the restaurant is closed Sunday and a fiche asks for consecutive rest
- **THEN** the wish is held only if Saturday or Monday is also a rest day that week

#### Scenario: Two non-adjacent closed days need a third rest
- **WHEN** two closed days in a week are not adjacent and a fiche asks for consecutive rest
- **THEN** the wish is held only if a third rest day is adjacent to one of the closed days

#### Scenario: Weekend radio and week labels
- **WHEN** one fiche has weekend even or odd
- **THEN** week_label_scheme is parity for the whole restaurant
- **WHEN** fiches only use every_two or no weekend wish
- **THEN** week_label_scheme is ab

#### Scenario: Zero evening and zero coupure caps
- **WHEN** a fiche sets max evening services to 0 or max coupures per week to 0
- **THEN** exceeding that cap produces the matching souhait warning

#### Scenario: Fill refuses exceeding max_services
- **WHEN** a fiche has `max_services.evening` 0
- **THEN** fill does not assign that person an evening shift
- **WHEN** `max_services` has no key for that service
- **THEN** fill does not treat that service as capped

#### Scenario: Fill scarce windows first
- **WHEN** two open windows have different static eligible counts
- **THEN** fill and hole-repair visit the window with fewer eligible people first
- **WHEN** eligible counts are equal
- **THEN** order is day_index, then restaurant service order, then post level descending

#### Scenario: Seeds lock then SAT then fill
- **WHEN** `generate_cycle` runs at optimized or maximal
- **THEN** it builds seeder locks, constrains SAT by those locks, fills remaining holes without moving locks, and keep-bests every seed × calendar
- **WHEN** a locked seed makes hard SAT infeasible
- **THEN** that seed is discarded and other seeds continue

#### Scenario: Minimal is empty plus sixteen calendars
- **WHEN** `generate_cycle` runs at minimal
- **THEN** there are no seed locks and at most 16 rest calendars

#### Scenario: Fill does not prefer a started day
- **WHEN** one person already has a shift that day with a gap to the trial and another person is free that day
- **THEN** fill prefers the person who does not create a coupure

#### Scenario: engine_ref is core-3
- **WHEN** `engine_ref()` is read
- **THEN** it equals `core-3`

#### Scenario: Unavailability is only the day-service pair
- **WHEN** a fiche has an unavailability for Tuesday midday
- **THEN** only that weekday and service is blocked

### Requirement: Employee board wishes follow posed wellbeing
The system SHALL expose one board wish row per posed wellbeing field, with held true when the published result has no matching souhait warning for that employee. The board MUST still use the published cycle only.

#### Scenario: Consecutive rest wish row
- **WHEN** a published salle cycle exists and the fiche has consecutive rest
- **THEN** the board has a consecutive_rest wish whose held flag follows the published warning code
