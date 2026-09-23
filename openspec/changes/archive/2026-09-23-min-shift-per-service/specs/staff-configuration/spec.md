# Spec Delta

## MODIFIED Requirements

### Requirement: Employee contract profile
The system SHALL store for each employee: name, role, skill level, team, contractual hours per week, and a minimum shift length in hours per offered company service (`morning`, `midday`, `evening`). The default minimum is 4 hours on every service. A missing service key or an unknown service SHALL use 4 hours. The restaurateur MAY lower or raise a service’s minimum independently. A stored minimum of 0 or less MUST be rejected. The map MUST NOT include a `continuous` key.

#### Scenario: Create a commis
- **WHEN** the restaurateur creates an employee named Sam, role commis, level 2, team cuisine, 35 contractual hours
- **THEN** the employee profile contains those values and a 4-hour minimum on every service

#### Scenario: Evening-only shorter minimum
- **WHEN** the restaurateur sets that employee’s evening minimum to 3 hours and leaves midday unset
- **THEN** evening uses 3 hours and midday uses 4 hours

## ADDED Requirements

### Requirement: Numeric min-shift in example and bench JSON
When hydrating staff from example or bench JSON, a numeric `min_shift_hours` of 4 or an omitted field MUST become an empty map (4 hours on every service). Any other positive number N MUST set N hours on each company service present in that draft. A mapping in JSON MUST be stored as a sparse per-service map. Saint-Cloud example JSON MUST NOT be rewritten for this change.

#### Scenario: Number 3 applies to the draft’s services
- **WHEN** a draft offers midday and evening and a fiche JSON has `min_shift_hours` 3
- **THEN** that fiche has a 3-hour minimum on midday and evening, and morning (absent from the draft) still defaults to 4 hours

#### Scenario: Number 4 stays the empty default
- **WHEN** a fiche JSON has `min_shift_hours` 4 or omits the field
- **THEN** that fiche’s minimum map is empty
