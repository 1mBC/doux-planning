## ADDED Requirements

### Requirement: Seed example context fills fiches without copying planning
`seed_example_context(state)` SHALL overwrite the restaurant’s employees from the Saint-Cloud file restaurant section, keep `identity.id`, `identity.name`, and `legal_context_id`, mint a new invite token per fiche that is not the fiche id, build one role ladder per team present on those fiches with unique `(name, level, team)` roles and `substitution_explained: true`, and clear `published_cycles`, `live_sandboxes`, `cycle`, and `accounts`. It MUST NOT copy planning assignments, MUST NOT call `generate_cycle` or `hydrate_delivered_cycle`, and MUST NOT rename the restaurant to Saint-Cloud.

#### Scenario: Empty restaurant seeded from Saint-Cloud
- **WHEN** `empty_restaurant("co-1")` is seeded
- **THEN** the name stays empty, at least one salle fiche exists, salle is ready and cuisine is not, published cycles are empty, each invite token differs from the fiche id, and the state has no assignments

#### Scenario: Seed again wipes a published cycle
- **WHEN** a restaurant already filled by seed and given a fake published cycle is seeded again
- **THEN** published cycles are empty and the fiches are the example fiches
