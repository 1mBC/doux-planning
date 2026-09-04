## Purpose

Exposes the frozen Saint-Cloud example as a public HTTP snapshot, with France legal rules loaded as a country context, and seeds that snapshot into the live database without running generation.

## ADDED Requirements

### Requirement: Public example snapshot endpoint
The system SHALL serve `GET /v1/examples/{example_id}` without authentication. For `saint-cloud` the response MUST be a JSON object with keys `example`, `legal`, `restaurant`, and `planning`. Unknown `example_id` MUST return HTTP 404 with a French error message. The endpoint MUST NOT require a session.

#### Scenario: Saint-Cloud is readable without auth
- **WHEN** an unauthenticated client calls `GET /v1/examples/saint-cloud`
- **THEN** the response is HTTP 200 with `example` equal to `saint-cloud` and the four required keys present

#### Scenario: Unknown example is not found
- **WHEN** a client calls `GET /v1/examples/inconnu`
- **THEN** the response is HTTP 404 and no planning body is returned

### Requirement: Legal context is a country document, not a restaurant field
The system SHALL load the legal rules from the country legal context named by the example’s `legal_context` (for Saint-Cloud: `france`). The `legal` object MUST include `id`, `kind` equal to `legal_context`, and the six default rule ids (`rest_between_days`, `weekly_rest_days`, `max_coupure`, `max_daily_cuisine`, `max_daily_salle`, `max_weekly_hours`). The `restaurant` object MUST NOT contain `legal_rules`. The restaurant MUST reference the context by id only (`legal_context: "france"` in the seed source).

#### Scenario: France is attached beside the restaurant
- **WHEN** the Saint-Cloud example is returned
- **THEN** `legal.id` is `france`, `legal.kind` is `legal_context`, and `restaurant` has no `legal_rules` key

#### Scenario: Missing legal context is a server failure
- **WHEN** an example names a legal context that is not stored
- **THEN** the endpoint returns HTTP 500 and does not invent legal rules on the restaurant

### Requirement: Example endpoint returns the stored snapshot, never a solve
Serving `GET /v1/examples/{example_id}` MUST read the snapshot already stored for that example. It MUST NOT run cycle generation, MUST NOT create a generation job, and MUST NOT recompute assignments, warnings, stats, legal rows, or wish rows.

#### Scenario: Stored Saint-Cloud planning is returned as-is
- **WHEN** the stored Saint-Cloud snapshot contains `planning.search_effort` `optimized` and `planning.stats.assignments` equal to 70
- **THEN** the HTTP body repeats those stored values even if a later live generate exists for the restaurant

#### Scenario: No generate on read
- **WHEN** the example endpoint is called
- **THEN** no generation job is created and the response time does not wait on a 14-day solve

### Requirement: Seed copies frozen data files into the live store
At boot or migrate, the system SHALL insert or refresh the France legal context from `data/legal/france.json` and the Saint-Cloud example (restaurant plus stored planning snapshot) from `data/examples/saint-cloud.json`. After seed, the public example endpoint MUST be satisfiable from the live store. The data files remain the frozen seed contract; they MUST NOT be read as a second runtime on each example request after seed has succeeded.

#### Scenario: Fresh database can serve Saint-Cloud
- **WHEN** the database is empty and boot or migrate runs
- **THEN** `GET /v1/examples/saint-cloud` returns the seeded snapshot with France legal context

#### Scenario: Runtime does not reread files as source of truth
- **WHEN** seed has completed and a client requests the example
- **THEN** the response is assembled from the live store (legal context row + stored snapshot), not by treating the JSON files as the live database
