# Spec Delta

## MODIFIED Requirements

### Requirement: Minimum shift length
Generation MUST NOT assign an employee to a post shorter than that employee’s minimum for the post’s service (`morning`, `midday`, or `evening`; default 4 when that key is absent). That minimum is per employee and per service, not a frozen global constant; a restaurateur MAY lower it on one service without changing the others. Posts are paired FIFO when remaining coverage still allows it (higher skill stays if the remaining posts need that skill). If the resulting window is still shorter than that service’s minimum, generation MUST stretch the shift to that minimum (extend the end first, then the start) within the service span, even if that overstaffs the tail of the service. An empty post is used only when the service span cannot fit the minimum. Having already worked another service that day MUST NOT authorize a shorter shift.

#### Scenario: FIFO opener leaves first
- **WHEN** two level-1 posts start at 10:00 and 11:00 and one level-1 leaves at 14:00
- **THEN** generation treats the 10:00 post as 10:00–14:00 and the 11:00 post as 11:00–15:00

#### Scenario: Higher-skill opener stays until close
- **WHEN** a level-3 opener starts at 18:00 and remaining coverage at 22:30 still includes a level-3 post
- **THEN** that opener’s window runs until the last departure of the service

#### Scenario: Three-hour closer is stretched
- **WHEN** an employee has the default 4-hour minimum and a closer post is 19:30–22:30 while the service continues until 24:00
- **THEN** generation assigns 19:30–23:30 rather than leaving the post empty

#### Scenario: Service too short stays empty
- **WHEN** an employee has the default 4-hour minimum and the whole service is only 3 hours
- **THEN** generation leaves that post unassigned

#### Scenario: Lower evening minimum fills a short closer
- **WHEN** an employee’s evening minimum is 3 hours, midday is unset, and a 19:30–22:30 evening closer is the whole evening service
- **THEN** generation assigns that 3-hour evening shift, and a 3-hour midday service still stays empty
