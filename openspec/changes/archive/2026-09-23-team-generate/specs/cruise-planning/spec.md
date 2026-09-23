## ADDED Requirements

### Requirement: Live restaurant publishes one cycle per team
The system SHALL store two independent published cycles on a live restaurant, one for salle and one for cuisine. An empty restaurant MUST have neither. Assignments in a team cycle MUST belong only to that team. The Saint-Cloud example cycle MUST remain the snapshot `cycle` field.

#### Scenario: Empty restaurant has no team cycles
- **WHEN** a restaurant is created empty
- **THEN** both salle and cuisine published cycles are absent

### Requirement: Generate one ready team without touching the other
The system SHALL generate a team cycle only when that team is ready. Generation MUST expand the typical week, draft only that team’s fiches and structures, and use the existing cycle solver with a search effort. If the team is not ready, generation MUST fail without solving. Regenerating a team MUST replace only that team’s published cycle.

#### Scenario: Salle ready generates salle only
- **WHEN** salle is ready and cuisine is not, and the restaurateur generates salle with minimal search
- **THEN** the salle published cycle has salle assignments only and cuisine stays unpublished

#### Scenario: Cuisine not ready does not solve
- **WHEN** cuisine is not ready and the restaurateur asks to generate cuisine
- **THEN** generation fails as team-not-ready and the solver is not called

#### Scenario: Second salle generate replaces salle
- **WHEN** salle already has a published cycle and the restaurateur generates salle again
- **THEN** the salle published cycle is replaced and cuisine remains unpublished
