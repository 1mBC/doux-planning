## ADDED Requirements

### Requirement: Remaining evaluate messages are French
`evaluate` MUST set the `message` of `contract_hours`, `consecutive_rest_days`, `weekend_rest_day`, `weekend_every_two_weeks`, `weekend_even_weeks`, `weekend_odd_weeks`, `unavailability`, `max_daily_hours`, `max_coupure`, `weekly_rest_days`, `max_weekly_hours`, and `assigned_on_closure` to the French forms in the live freeze. Hours MUST use the `_hours_label` shape (`29h` / `11h30`). Weekdays, services, and week labels MUST use the same helpers as `empty_post`. `severity`, `code`, and `day_index` MUST stay unchanged. `contract_hours` MUST stay `souhait`. Messages already in French (`empty_post`, `max_mornings` / `max_middays` / `max_evenings`, `max_coupures`, `rest_between_days`) MUST stay as they are.

#### Scenario: Contract hours warning
- **WHEN** a week’s assigned hours miss the contractual weekly hours
- **THEN** the `contract_hours` message contains `contrat` and `sem.`

#### Scenario: Consecutive rest warning
- **WHEN** a fiche with `consecutive_rest` has no two consecutive rest days in a week
- **THEN** the `consecutive_rest_days` message contains `pas deux repos consécutifs`

#### Scenario: Unavailability warning
- **WHEN** a person is assigned on a blocked weekday/service
- **THEN** the `unavailability` message contains `posé sur indispo` and the French day and service
