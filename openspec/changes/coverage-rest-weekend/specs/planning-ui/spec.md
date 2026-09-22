# Spec Delta

## ADDED Requirements

### Requirement: every_two copy is at least one weekend
The client SHALL label `weekend: every_two` as at least one full weekend off in 14 days, not as exactly one. Recap title MUST be « Au moins un week-end / 14 j. ». A miss fact MUST read « aucun week-end complet off / 14 j. ». Wizard radio and employee-board wish MUST say « Au moins un we sur deux ».

#### Scenario: Dictionary and radio
- **WHEN** the restaurateur opens wellbeing or a recap cell for `weekend_every_two_weeks`
- **THEN** the visible French does not say “exactly one weekend off”
