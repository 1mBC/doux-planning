# Spec Delta

## ADDED Requirements

### Requirement: Retiring a fiche unpublishes only that employee’s team
The system SHALL, when a staff fiche is retired, drop that employee’s team published cycle and live sandbox. The other team’s published cycle and live sandbox MUST stay intact. Types, typical week, role ladders, hours, and week-label scheme MUST NOT be rewritten as part of the retirement.

#### Scenario: Remove salle unpublishes salle and keeps cuisine
- **WHEN** salle and cuisine each have a published cycle, salle has an open live sandbox, and the restaurateur retires a salle fiche
- **THEN** the salle published cycle and salle live sandbox are absent, and the cuisine published cycle remains
