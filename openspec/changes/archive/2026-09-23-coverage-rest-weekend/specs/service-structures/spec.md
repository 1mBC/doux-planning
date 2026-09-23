# Spec Delta

## MODIFIED Requirements

### Requirement: Departure waves
For each team and service structure, the system SHALL record an ordered sequence of departures: time of departure (on a 15-minute grid), how many people leave, and which post levels MUST remain present after that departure. The last remaining bag MAY be non-empty: those leftover posts MUST stay until that last wave’s clock (and never leave before the first departure of the structure). Coverage slices MUST include them for every interval they are still listed. Waves need not end with an empty remaining bag.

#### Scenario: First departures leave coverage
- **WHEN** the restaurateur sets a 14:30 departure of two people and requires at least one level-4 and one level-2 post to remain
- **THEN** after 14:30 the structure’s remaining posts include those minimum levels until later departures

#### Scenario: Leftover chef after last departure
- **WHEN** MIDI arrivals are L1 10:00, L3 10:30, L2 11:30 and departures are 15:30 remaining `[1,3]` then 16:00 remaining `[3]`
- **THEN** the L3 window is 10:30–16:00 (not 10:30–14:30), the first real leave is still 15:30, and slices from 10:30 to 16:00 include level 3
