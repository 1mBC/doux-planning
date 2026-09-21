# Spec Delta

## ADDED Requirements

### Requirement: Restaurateur can retire a staff fiche
The system SHALL let the restaurateur remove an existing staff fiche from the restaurant. Removal MUST drop that fiche from the restaurant staff list and MUST drop that fiche id from the restaurant’s linked-employee set when it was present. An unknown fiche id MUST fail as unknown-employee. Redeeming an invite MUST keep its current company-code and fiche-or-token behaviour so an existing account can be re-linked later. Platform accounts, sessions, and email are out of scope.

#### Scenario: Salle fiche leaves the staff list and linked set
- **WHEN** a restaurant has a salle fiche and a cuisine fiche, both ids are in the linked-employee set, and the restaurateur retires the salle fiche
- **THEN** the salle fiche is absent from the staff list, the salle id is absent from the linked-employee set, and the cuisine fiche remains

#### Scenario: Unknown fiche id is rejected
- **WHEN** the restaurateur retires a fiche id that is not on the restaurant
- **THEN** removal fails as unknown-employee and the staff list is unchanged
