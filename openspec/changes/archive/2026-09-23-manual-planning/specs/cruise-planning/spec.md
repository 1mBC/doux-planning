# Spec Delta

## ADDED Requirements

### Requirement: Ready team can seed an empty published cycle
The system SHALL let the restaurateur publish a ready team's cruise cycle as an empty grid (that team's structures and staff, zero assignments) scored for coverage, legal, contract, and wellbeing, without running the solver. A team that is not ready MUST fail as not-ready and MUST NOT write a published cycle. The other team's published cycle MUST stay unchanged.

#### Scenario: Ready salle seeds empty grid, cuisine stays unpublished
- **WHEN** salle is ready and has no generated cycle, and the restaurateur seeds an empty salle cycle
- **THEN** salle published assignments are empty, scoring reports empty-post coverage warnings, and cuisine stays unpublished

#### Scenario: Team not ready cannot seed
- **WHEN** cuisine is not ready and the restaurateur seeds an empty cuisine cycle
- **THEN** seeding fails as team-not-ready and neither team's published cycle is written

### Requirement: Empty seed is a published cycle for live edit
The system SHALL treat the empty seeded cycle as a published cycle for live enter. Existing fill, apply, and undo gestures MUST work on that draft. A later generate for that team MUST replace that team's Core published slot. The Saint-Cloud example sandbox MUST stay unchanged.

#### Scenario: Fill apply undo on the empty seed
- **WHEN** salle is seeded empty, the restaurateur enters the salle live sandbox, fills a post, applies, then undoes
- **THEN** assignments return to empty and history is empty, without invoking the solver

#### Scenario: Generate after seed replaces the salle slot
- **WHEN** salle has an empty seeded cycle and the restaurateur generates salle with minimal effort
- **THEN** the salle published cycle has generated assignments and cuisine stays unpublished
