## ADDED Requirements

### Requirement: Empty restaurant has a name and country legal context
The system SHALL create an empty restaurant with an empty display name and a country legal-context id defaulting to `france`. The legal rules MUST NOT be copied onto the restaurant or its fiches. The empty restaurant MUST have no employee fiches and no published cycle.

#### Scenario: Empty restaurant is not ready
- **WHEN** a restaurant is created empty
- **THEN** it has an empty name, legal-context id `france`, no fiches, no published cycle, and neither team is ready to calculate

### Requirement: A team is ready only when its staff and ladder exist
`team_ready` for a team MUST require a role ladder for that team and at least one employee fiche on that team. Salle MAY be ready while cuisine is not. One fiche belongs to exactly one team. Contract hours and unavailabilities are restaurateur-owned; wellbeing preferences are souhaits. Minimum shift length defaults to 4 hours.

#### Scenario: Salle staffed, cuisine empty
- **WHEN** the empty restaurant has a salle ladder, one salle fiche, company services, salle types, and a fully typed open typical week for salle
- **THEN** salle is ready to calculate and cuisine is not
