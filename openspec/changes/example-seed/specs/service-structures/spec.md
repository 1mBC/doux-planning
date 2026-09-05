## ADDED Requirements

### Requirement: Seed maps example structures onto types and a typical week
`seed_example_context` SHALL set company services and hours from the example restaurant hours, turn each example structure into a `ServiceType` (same id, team, service, waves; name defaults to id), and build a typical week for every team × company service × weekday: an open cell with that structure’s id when a matching structure lists the weekday, otherwise a closed cell with no type. `state.structures` MUST be `expand_typical_week` after that mapping, not the raw example structures alone.

#### Scenario: Seeded Saint-Cloud has services, types, and a typical week
- **WHEN** an empty restaurant is seeded from Saint-Cloud
- **THEN** company services are midday and evening, types and a typical week exist, and expanded structures cover the open salle cells
