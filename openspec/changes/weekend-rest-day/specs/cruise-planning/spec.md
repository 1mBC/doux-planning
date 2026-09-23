## ADDED Requirements

### Requirement: Weekend rest day is a per-week Saturday-or-Sunday off
The system SHALL store `weekend_rest_day` as a boolean defaulting to false, independent of the `weekend` radio. When the box is posed, each week of the cycle MUST have Saturday or Sunday off. A fully closed restaurant weekday MUST count as rest. The matching souhait warning code SHALL be `weekend_rest_day`. The rest solver MUST aim at this wish. Hydrate MUST read the object bool (absent → false) and MUST still reject the legacy list key `at_least_one_weekend_rest_day`.

#### Scenario: Sunday closed holds the wish
- **WHEN** Sunday is closed and a fiche has `weekend_rest_day: true`
- **THEN** the wish is held without another weekend rest day

#### Scenario: Both weekend days worked warns
- **WHEN** Sunday is open and the employee works Saturday and Sunday in a week
- **THEN** evaluate emits souhait `weekend_rest_day`

#### Scenario: Stacks with weekend even
- **WHEN** a fiche has `weekend_rest_day: true` and `weekend: even`
- **THEN** the two wishes are scored with distinct codes

### Requirement: Board exposes a posed weekend rest day
`employee_board` SHALL include `{ kind: "weekend_rest_day", held }` only when the box is posed. Held follows the published `weekend_rest_day` souhait warning. An absent hydrate key MUST NOT add a board row.

#### Scenario: Posed box appears on the board
- **WHEN** a published cycle exists and the fiche has `weekend_rest_day: true`
- **THEN** the board has a weekend_rest_day wish whose held flag follows the published warning
