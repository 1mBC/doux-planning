## Purpose

Makes PostgreSQL the live source of truth for one restaurant’s domain data, including the seeded Saint-Cloud example and France legal context, without turning data files into a second runtime.

## ADDED Requirements

### Requirement: Live store holds the domain
The system SHALL persist in the live database: restaurant identity and invite code, staff (roles, employees, contracts, unavailabilities, wellbeing), service structures, opening hours, published cycle, calendar weeks, intents, at most one sandbox per restaurant, legal contexts, restaurateur and employee accounts, sessions, and generation jobs. After a process restart, those records MUST still be readable without regenerating a cycle.

#### Scenario: Restart keeps published cycle
- **WHEN** a restaurant has a published cycle and the API process restarts
- **THEN** a subsequent restaurateur read returns the same published assignments and warnings

#### Scenario: Sandbox survives leave
- **WHEN** the restaurateur enters a cycle sandbox, edits, and the session later returns
- **THEN** the same unpublished sandbox draft is still present until discard or publish

### Requirement: Restaurant references legal context by id
Each restaurant SHALL store a `legal_context` identifier (Saint-Cloud: `france`). Legal rule documents SHALL live in legal-context records, not copied onto the restaurant row. Loading a restaurant MUST resolve displayable legal rules from that context.

#### Scenario: Saint-Cloud points at France
- **WHEN** the seeded restaurant is read
- **THEN** its `legal_context` is `france` and its stored restaurant document does not embed a `legal_rules` array

### Requirement: Data files are seed input only
`data/legal/*.json` and `data/examples/*.json` SHALL be applied at boot or migrate to insert the France context and the Saint-Cloud restaurant plus its frozen planning snapshot. After seed, live reads and writes MUST go to the database. Changing live staff or publishing a new cycle MUST NOT rewrite the data files.

#### Scenario: Live edit does not mutate the seed file
- **WHEN** the restaurateur updates an employee’s contractual hours in the live restaurant
- **THEN** `data/examples/saint-cloud.json` is unchanged

### Requirement: Frozen example snapshot is stored separately from live planning
The system SHALL store the Saint-Cloud public snapshot independently of later live generation or publish. Public example reads MUST use that stored snapshot. Restaurateur live reads MUST use the live published cycle or sandbox, not the frozen snapshot, once live state exists.

#### Scenario: Generate does not overwrite the public example
- **WHEN** the restaurateur completes a generation job that differs from the seeded snapshot
- **THEN** `GET /v1/examples/saint-cloud` still returns the frozen seeded snapshot

#### Scenario: Live published planning is distinct
- **WHEN** the restaurateur publishes a new cycle
- **THEN** restaurateur cycle reads return the newly published result and the public example snapshot is unchanged

### Requirement: Live companies are distinct from the Saint-Cloud snapshot
A `kind: company` register SHALL insert a new live company row (empty name, Core invite code) and MUST NOT reuse the seeded `restaurants` / `example_snapshots` Saint-Cloud row. Each company session is bound to that live company id. The system MUST NOT expose a restaurant-collection picker in this change.

#### Scenario: No restaurant picker
- **WHEN** a restaurateur session is issued
- **THEN** it is bound to the live company created at register (or the employee’s linked company) and no restaurant-collection route exists

#### Scenario: Company register does not attach to Saint-Cloud
- **WHEN** a caller registers `kind: company`
- **THEN** `me.restaurant_id` is not the seeded Saint-Cloud restaurant id and `GET /v1/examples/saint-cloud` is unchanged
