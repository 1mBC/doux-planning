## Purpose

Permet au restaurateur de décrire comment le restaurant tourne : mode continu ou par services, fermetures, et structures de couverture par vagues d’arrivée et de départ, applicables à des jours de la semaine.

## ADDED Requirements

### Requirement: Continuous or multi-service mode
The system SHALL let the restaurateur choose continuous service (treated as a single service) or a set of named services such as morning, midday, and evening.

#### Scenario: Continuous restaurant
- **WHEN** the restaurateur selects continuous service
- **THEN** staffing structures are defined against one service that spans the opening day

#### Scenario: Three services
- **WHEN** the restaurateur selects morning, midday, and evening services
- **THEN** each service can have its own staffing structure per team

### Requirement: Closures
The system SHALL record closed days and closed services so that no coverage is required and no employee is assigned on those slots.

#### Scenario: Monday closed
- **WHEN** the restaurateur marks Monday as closed
- **THEN** generated and published plannings have no shifts on Monday

### Requirement: Arrival waves
For each team and service structure, the system SHALL record an ordered sequence of arrivals: time of arrival (on a 15-minute grid), how many people arrive, and which post levels those arrivals must fill.

#### Scenario: Kitchen midday opening
- **WHEN** the restaurateur sets cuisine midday arrivals as 10:00 one level-4 post, then 11:00 two level-2 posts, then 11:30 one level-1 post
- **THEN** that structure requires those posts to be occupied from those times onward until matching departures

### Requirement: Departure waves
For each team and service structure, the system SHALL record an ordered sequence of departures: time of departure (on a 15-minute grid), how many people leave, and which post levels MUST remain present after that departure. Waves continue until the service is empty.

#### Scenario: First departures leave coverage
- **WHEN** the restaurateur sets a 14:30 departure of two people and requires at least one level-4 and one level-2 post to remain
- **THEN** after 14:30 the structure’s remaining posts include those minimum levels until later departures

### Requirement: Structure applies to weekdays
Once a service structure is defined, the system SHALL ask which weekdays it applies to, and MUST explain that a different structure can be defined for days that run differently. The restaurateur MUST be able to cover every open (team, service, weekday) combination with a structure.

#### Scenario: Weekday vs weekend kitchen
- **WHEN** the restaurateur applies a cuisine midday structure to Monday–Friday and a different cuisine midday structure to Saturday–Sunday
- **THEN** generation uses the weekday structure on Friday and the weekend structure on Saturday

### Requirement: Fifteen-minute time quantum
The system SHALL represent arrival, departure, and shift boundaries on a 15-minute grid.

#### Scenario: Half-past arrival
- **WHEN** the restaurateur sets an arrival at 11:30
- **THEN** the system accepts it and rejects a time not aligned to 15 minutes

### Requirement: Suggested structure templates
The system SHALL offer optional pre-filled service-structure templates the restaurateur can adjust, so that onboarding does not require building every wave from an empty form.

#### Scenario: Start from a template
- **WHEN** the restaurateur picks a template for a service-based brasserie
- **THEN** arrival and departure waves are pre-filled and remain editable
