## ADDED Requirements

### Requirement: Company services may be none
The system SHALL store the restaurant’s chosen services as zero or more of morning, midday, and evening. An empty restaurant has none. Existing restaurants that already have opening hours (Saint-Cloud) MUST keep those hours.

#### Scenario: Empty restaurant has no company services
- **WHEN** a restaurant is created empty
- **THEN** it has no chosen company services and is not ready to calculate

### Requirement: Named service types hold waves
The system SHALL let the restaurateur define named service types, each for one team and one service, with the same arrival and departure waves as existing structures. Types do not carry weekdays; days come from the typical week.

#### Scenario: Type without weekdays
- **WHEN** the restaurateur upserts a salle midday type with arrival and departure waves
- **THEN** that type stores those waves and no weekday set

### Requirement: Typical week expands to identical fortnight structures
The system SHALL store a typical week of cells (weekday, service, optional type, closed). Expanding that week MUST produce service structures whose weekdays come from open cells, and week A MUST equal week B (days 0–6 match 7–13). An open cell without a valid type for that team MUST make the team not ready.

#### Scenario: Expand copies week A to week B
- **WHEN** a typical week is expanded
- **THEN** the structures that would apply to week A equal those that would apply to week B

#### Scenario: Open cell missing a type
- **WHEN** a salle typical-week cell is open and has no type
- **THEN** salle is not ready to calculate
