## Purpose

Generates a published 14-day cycle **per team** over HTTP by wrapping Core `generate_team` synchronously, and persists the two independent published cycles for the live company.

## ADDED Requirements

### Requirement: Generate is a synchronous generate_team wrap
`POST /v1/generate` (Bearer company) SHALL accept `{ team: "salle"|"cuisine", search_effort?: "minimal"|"optimized"|"maximal" }` and MUST call Core `generate_team` in the request. Omitted `search_effort` MUST default to `optimized`. HTTP tests in this slice MUST use `minimal` only. The 200 body MUST be `{ team, search_effort, published }` where `published` has `salle` and `cuisine` keys, each `null` or `{ assignments, warnings, stats, legal_cols, legal_rows, wish_cols, wish_rows }`. Assignments and warnings MUST be serialized from that team’s `EngineResult`. Recap keys MUST be Core `cycle_recap` (no invented counts or cells, no `we1j`). A `null` cycle MUST omit recap keys. The system MUST NOT enqueue a job, MUST NOT start a worker, and MUST NOT use `SKIP LOCKED`.

#### Scenario: Salle generate when ready
- **WHEN** the live context is salle-ready and the restaurateur posts generate with `team` `salle` and `search_effort` `minimal`
- **THEN** the response is HTTP 200, `published.salle.assignments` is non-empty, every assignment has `team` `salle`, `published.salle.stats.assignments` equals that length, `legal_rows` and `wish_cols` are present, `wish_cols` has no `we1j`, and `published.cuisine` is `null`

#### Scenario: Cuisine not ready
- **WHEN** only salle is ready and the restaurateur posts generate for `cuisine`
- **THEN** the response is HTTP 409 with French `detail` `Cette équipe n'est pas prête à calculer.`, no solver run, and persisted cycles are unchanged

#### Scenario: Invalid team or effort
- **WHEN** `team` or `search_effort` is missing or unknown
- **THEN** the response is HTTP 400 `Champs invalides.`

### Requirement: Regenerating one team leaves the other intact
A second successful generate for a team SHALL replace only that team’s published cycle. The other key MUST stay as previously persisted (or `null`).

#### Scenario: Second salle generate
- **WHEN** salle has already been generated and the restaurateur posts generate salle again
- **THEN** `published.salle` is the new result and `published.cuisine` remains `null` (or the previous cuisine cycle if one existed)

### Requirement: GET cycles reads persisted published cycles
`GET /v1/cycles` (Bearer company) SHALL return `{ published: { salle, cuisine } }` from the live store, including persisted `cycle_recap` keys on each non-null cycle. A restaurant that has never generated MUST return both keys `null`. After `reset_engine` / process restart, the body MUST match the last persisted generate. A stored cycle missing recap keys MUST be hydrated and passed to Core `cycle_recap` (no HTTP 500). The endpoint MUST NOT call `generate_team` or `generate_cycle`.

#### Scenario: Never generated
- **WHEN** a company session gets `/v1/cycles` before any generate
- **THEN** `published.salle` and `published.cuisine` are `null`

#### Scenario: Restart keeps cycles
- **WHEN** salle has been generated and the API engine is reset
- **THEN** `GET /v1/cycles` returns the same `published` object

#### Scenario: Stored cycle without recap hydrates
- **WHEN** JSONB already has a salle cycle with only `assignments` and `warnings`
- **THEN** `GET /v1/cycles` is HTTP 200 and `published.salle` includes Core `cycle_recap` keys

### Requirement: Auth and public surfaces stay unchanged
Generate and cycles SHALL require a company session. An employee session MUST receive HTTP 403 `Action réservée au restaurateur.` Missing/invalid Bearer MUST be HTTP 401 `Session invalide.` Without `DATABASE_URL` those routes MUST be HTTP 503 `Base indisponible.` `GET /v1/examples/saint-cloud` MUST stay 200 with 92 assignments. Public sandbox and context GET/auth MUST stay green. Persist MUST NOT write `example_snapshots` or `data/examples/saint-cloud.json`.

#### Scenario: Employee cannot generate
- **WHEN** an employee session posts `/v1/generate`
- **THEN** the request is rejected with HTTP 403 and no cycle is written
