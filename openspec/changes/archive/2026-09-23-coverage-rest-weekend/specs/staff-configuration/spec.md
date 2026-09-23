# Spec Delta

## MODIFIED Requirements

### Requirement: Wellbeing preferences
The system SHALL record, per employee, the following wellbeing preferences (others MAY be added in a later change): prefer two consecutive rest days **on weekdays** (Monday–Friday, e.g. Tuesday–Wednesday); **at least one** weekend off every two weeks; at least one rest day each weekend; no evening service; no morning service; at most two coupures per week; at most three coupures per week. Two consecutive rest days MUST NOT be satisfied by Saturday–Sunday or Sunday–Monday; those are the weekend preferences, a different rule. `every_two` is held when at least one of the two weekends (Saturday+Sunday) is fully off, including when both are off or the plan is empty.

#### Scenario: Consecutive rest days preference
- **WHEN** the restaurateur enables “two consecutive rest days” for an employee
- **THEN** the constraint engine treats that preference as a souhait-level constraint for two adjacent weekdays, not as a weekend off

#### Scenario: At least one weekend off
- **WHEN** a fiche has `weekend: every_two` and the cycle has no shifts
- **THEN** `weekend_every_two_weeks` is held
- **WHEN** both weekends have at least one shift
- **THEN** `weekend_every_two_weeks` is a souhait miss
