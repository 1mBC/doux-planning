## Purpose

Generates a published 14-day cycle **per team** over HTTP by wrapping Core `generate_team`: `minimal` / `optimized` stay synchronous; `maximal` is a Postgres job claimed by a worker (`SKIP LOCKED`).

## ADDED Requirements

### Requirement: Generate is hybrid C
`POST /v1/generate` (Bearer company) SHALL accept `{ team: "salle"|"cuisine", search_effort?: "minimal"|"optimized"|"maximal" }`. Omitted `search_effort` MUST default to `optimized` and MUST stay a **200** in-request `generate_team` wrap. `minimal` / `optimized` MUST call Core `generate_team` in the web process and MUST NOT insert a `generate_jobs` row. The 200 body MUST be `{ team, search_effort, published }` where `published` has `salle` and `cuisine` keys, each `null` or `{ versions: { minimal, optimized, maximal }, latest }` per `contracts/domain/generate-versions.md`. Each non-null version MUST be `{ assignments, warnings, stats, legal_cols, legal_rows, wish_cols, wish_rows, generated_at, search_effort }`. Assignments and warnings MUST be serialized from that team’s `EngineResult`. Recap keys MUST be Core `cycle_recap` (no invented counts or cells, no `we1j`). A never-generated team MUST stay `null`. POST MUST write only `versions[effort]` and recompute `latest`. `maximal` MUST return HTTP 202 `{ job_id, team, search_effort: "maximal", status: "queued", estimated_seconds: 600 }` with no `published` and MUST NOT call `generate_team` in uvicorn. HTTP sync tests MUST use `minimal`. Job tests MUST tick an exported worker function with `generate_team` stubbed (0 s) and MUST NOT wait 600 s.

#### Scenario: Salle generate when ready
- **WHEN** the live context is salle-ready and the restaurateur posts generate with `team` `salle` and `search_effort` `minimal`
- **THEN** the response is HTTP 200, `published.salle.versions.minimal.assignments` is non-empty, every assignment has `team` `salle`, that cycle’s `stats.assignments` equals that length, `legal_rows` and `wish_cols` are present, `wish_cols` has no `we1j`, `latest` is `minimal`, and `published.cuisine` is `null`

#### Scenario: Flat stored cycle is coerced
- **WHEN** JSONB still has a flat salle cycle (no `versions`)
- **THEN** GET cycles returns `versions.optimized` equal to that cycle, `latest` `optimized`, and no flat assignments at the team root

#### Scenario: Two efforts keep both slots
- **WHEN** the restaurateur posts salle `minimal` then salle `optimized`
- **THEN** both slots are present, `latest` is `optimized`, and the minimal cycle is unchanged

#### Scenario: Cuisine not ready
- **WHEN** only salle is ready and the restaurateur posts generate for `cuisine`
- **THEN** the response is HTTP 409 with French `detail` `Cette équipe n'est pas prête à calculer.`, no solver run, no `generate_jobs` row, and persisted cycles are unchanged

#### Scenario: Maximal enqueue
- **WHEN** salle is ready and the restaurateur posts generate with `search_effort` `maximal`
- **THEN** the response is HTTP 202, `status` is `queued`, `estimated_seconds` is 600, `published` is absent, and `generate_team` was not called in the request

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

### Requirement: Successful generate is logged
A `POST /v1/generate` HTTP 200 SHALL insert one `generate_logs` row `{ email, restaurant_name, team, warnings }` for the team just solved. A worker job that reaches `done` MUST insert the same log. HTTP 409 `TeamNotReady` and a `failed` job MUST NOT insert a row. `GET /v1/admin/generates` MUST return those rows newest-first.

#### Scenario: Ready generate writes a log
- **WHEN** salle is ready and generate returns 200
- **THEN** one log row is stored with that team’s HTTP `warnings`

#### Scenario: Not-ready generate writes nothing
- **WHEN** generate returns HTTP 409
- **THEN** `generate_logs` is unchanged

### Requirement: Maximal job poll and worker tick
`GET /v1/generate/jobs/{job_id}` (Bearer company, same restaurant) SHALL return `{ job_id, team, search_effort, status, estimated_seconds }` with `status` `queued` | `running` | `done` | `failed`. `published` MUST appear only when `status` is `done` and MUST match `GenerateResult.published`. `error` MUST appear only when `failed`. Another company’s session or an unknown id MUST be HTTP 404. An employee session MUST be HTTP 403. The worker SHALL claim one `queued` row with `SELECT … FOR UPDATE SKIP LOCKED`, set `running`, call `generate_team(…, maximal)`, persist `published_cycles` like a 200, then set `done`. A second `maximal` for the same company+team while `queued` or `running` MUST be HTTP 409 `Un calcul maximal est déjà en cours.`

#### Scenario: Tick stub completes a maximal job
- **WHEN** a salle maximal job is `queued` and the test calls one worker tick with `generate_team` stubbed
- **THEN** GET job is `done` with `published.salle` present and one new `generate_logs` row

#### Scenario: Second maximal while queued
- **WHEN** a salle maximal job is already `queued` and the restaurateur posts maximal salle again
- **THEN** the response is HTTP 409 `Un calcul maximal est déjà en cours.`
