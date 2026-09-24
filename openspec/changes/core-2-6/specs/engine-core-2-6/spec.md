# Spec Delta

## Purpose

core-2.6 places weekend rests across both weeks, prefers staff still under contract, and keeps each shift on the service-type window.

## ADDED Requirements

### Requirement: Weekend rests are split across the two weeks
The engine SHALL lock an even-weekend wish onto week A and an odd-weekend wish onto week B. Each every-other-weekend wish SHALL be off exactly one of the two weekends. Among staff who have one of these three wishes, the number off on weekend A and the number off on weekend B SHALL differ by at most 1 whenever the even and odd locks allow it. Staff with no weekend wish SHALL remain free to work both weekends. A weekend off SHALL mean no shift on that Saturday and that Sunday.

#### Scenario: Four every-other-weekend wishes
- **WHEN** four staff have an every-other-weekend wish and nobody has an even or odd wish
- **THEN** two of them are off weekend A and the other two are off weekend B

#### Scenario: Even and odd wishes stay locked
- **WHEN** one staff member has an even wish, one has an odd wish, and two have an every-other-weekend wish
- **THEN** the even wish is off week A and works week B, the odd wish is off week B and works week A, and the two every-other wishes are placed so the two weekend counts differ by at most 1

#### Scenario: No weekend wish
- **WHEN** a staff member has no weekend wish
- **THEN** the engine does not force that person off either weekend

### Requirement: Contract overrun is allowed only when nobody under contract can take the post
For a post, the engine SHALL build the pool of staff who are available for that post: sufficient level, not on a rest day, no overlap, 11 hours of rest, and within the evening and split-shift caps. If at least one person in that pool is strictly under their weekly contract before the shift, the engine SHALL choose only from those people. If none are under contract, the engine SHALL allow a person already at or above their contract to take the post.

#### Scenario: Someone under contract is available
- **WHEN** two staff can take the post and only one is under their weekly contract
- **THEN** the person under contract receives the post

#### Scenario: Only one person can take the post
- **WHEN** the only available person would go over their weekly contract by taking the post
- **THEN** that person receives the post

### Requirement: Hours are balanced inside the same level and contract
Inside the pool selected for a post, the engine SHALL choose the person with the lowest ratio of hours already worked that week to their contract. Ties SHALL go to the closest level at or above the post. After the fill, for each week and each group of the same level and the same contract, while two people differ by more than half an hour, the engine SHALL move one shift from the person with more hours to the person with fewer hours when the receiver can hold that shift without breaking a rest day, the 11-hour rest, or a cap, and without the receiver ending above the giver.

#### Scenario: Lower ratio wins
- **WHEN** two staff of the same level and the same contract can take the post and one has worked fewer hours toward that contract
- **THEN** the person with the lower ratio receives the post

#### Scenario: Transfer closes a gap above half an hour
- **WHEN** after the fill two staff of the same level and the same contract differ by more than half an hour on a week and a legal transfer exists
- **THEN** the engine moves a shift that reduces the gap and leaves the receiver at or below the giver

### Requirement: Weekday rest keeps the largest remaining crew
After weekend rests are fixed, each remaining legal rest day SHALL be placed on an open day that is not a weekend the person must work, choosing the day whose surplus is highest. Surplus of a day SHALL be the smallest gap, across that day's services, between coworkers still present who can hold at least one post and the number of posts. If every surplus is negative, the engine SHALL still place the rest day on the least negative day.

#### Scenario: A day with more remaining staff is preferred
- **WHEN** a person still owes one weekday rest and one open day would leave more coworkers than posts while another would leave fewer
- **THEN** the rest is placed on the day with the higher surplus

### Requirement: The shift clock is the service-type window
The engine SHALL assign the start and end of the service-type window. It SHALL prefer staff whose minimum shift fits inside that window. When nobody available has a minimum that fits, the engine SHALL still assign that same window, shorter than the minimum. The engine SHALL NOT extend the shift to reach the minimum.

#### Scenario: Someone fits the window
- **WHEN** at least one available person has a minimum shift no longer than the window
- **THEN** the assigned shift starts and ends at the window bounds and the person is chosen from those who fit

#### Scenario: Nobody fits the window
- **WHEN** every available person has a minimum shift longer than the window
- **THEN** the assigned shift still starts and ends at the window bounds

### Requirement: core-2.6 is registered and is not the fallback
The engine registry SHALL include `core-2.6` immediately after `core-2.5`. The last registry name SHALL remain `mix-0`. `mix-0` SHALL NOT call `core-2.6`.

#### Scenario: Registry order
- **WHEN** the engine list is read
- **THEN** `core-2.6` follows `core-2.5` and `mix-0` is last
