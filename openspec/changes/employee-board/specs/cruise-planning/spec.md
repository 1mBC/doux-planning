## ADDED Requirements

### Requirement: Employee board shows the published team grid
The system SHALL expose a read-only employee board for a known fiche. The board MUST include every assignment from that team’s published cycle, not only the viewer’s shifts. If the team has no published cycle, assignments MUST be empty. An unknown fiche MUST fail as unknown-employee. The board MUST NOT read a live sandbox draft.

#### Scenario: Salle board includes every published salle assignment
- **WHEN** salle is generated and the restaurateur opens the board for a salle employee who has a wish
- **THEN** the board assignments are the full published salle cycle

#### Scenario: Unpublished live edit is invisible
- **WHEN** a live salle sandbox has an applied unpublished edit
- **THEN** the salle employee board still matches the published cycle

#### Scenario: Cuisine without a published cycle is empty
- **WHEN** a cuisine fiche exists and cuisine has no published cycle
- **THEN** that employee’s board assignments are empty

#### Scenario: Unknown fiche is rejected
- **WHEN** the board is requested for an id that is not on the staff list
- **THEN** the request fails as unknown-employee

### Requirement: Employee board contract and wishes are read-only
The system SHALL report contract weekly hours, assigned hours for that employee on the published cycle (zero if unpublished), and whether contract is ok. Wish rows MUST come only from fiche wellbeing keys. A wish is held when the published result has no matching souhait warning for that employee and mapped code. Unavailabilities MUST be the fiche patterns. The system MUST NOT generate a cycle to build the board.

#### Scenario: Wish held follows published souhait warnings
- **WHEN** the fiche has a wellbeing preference
- **THEN** the board has that wish row and held is false if the published result has a matching souhait warning for that employee, true otherwise
