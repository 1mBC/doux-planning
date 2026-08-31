## Purpose

Fournit un moteur unique qui génère un cycle, évalue un planning, classe des candidats et produit des warnings, en respectant postes, légal, contrat, indisponibilités et bien-être.

## ADDED Requirements

### Requirement: Exclusive posts with nearest-level descent
Coverage MUST be a set of exclusive posts at required levels. The engine SHALL fill each post with an employee whose level is greater than or equal to the post level, preferring exact match, then the nearest higher level. A person occupies exactly one post for their entire shift. The only holder of a high post MUST NOT be assigned to a lower post if that would leave the high post empty.

#### Scenario: Second chef fills sous-chef
- **WHEN** needed posts are chef, sous-chef, two commis, one plongeur, and available people are two chefs, one sous-chef, one commis, and no plongeur
- **THEN** one chef fills chef, the other chef fills sous-chef, sous-chef fills a commis post, commis fills commis, and the plongeur post remains empty

#### Scenario: Sole chef stays chef
- **WHEN** only one level-4 employee is present and both a chef post and a plongeur post are unfilled
- **THEN** that employee is assigned to the chef post, not the plongeur post

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
The engine SHALL take contractual weekly hours into account when generating and scoring. Missing or exceeding contractual hours MUST produce a warning (souhait unless a later change tightens this).

#### Scenario: Under-scheduled part-timer
- **WHEN** an employee with 20 contractual hours is assigned 8 hours in a cycle week
- **THEN** the engine reports a warning on that employee’s hours

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
