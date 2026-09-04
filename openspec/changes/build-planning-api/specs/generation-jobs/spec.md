## Purpose

Wraps 14-day cycle generation in a pollable job so the client can show an estimated wait without streaming the solver or blocking on an immediate engine result.

## ADDED Requirements

### Requirement: Generate creates a job, not an immediate engine result
`POST` generate (restaurateur, cycle sandbox) SHALL enqueue a generation job and return HTTP 202 (or 200 with job metadata only) containing `job_id`, `status`, `search_effort`, and `estimated_seconds`. The response MUST NOT include the generated assignments or warnings. `search_effort` MUST be `minimal`, `optimized`, or `maximal`, defaulting to `optimized` when omitted. `estimated_seconds` MUST be the engine’s existing per-effort time bound for that value (not a second scoring model and not a live remaining-time stream).

#### Scenario: Optimized generate is accepted as a job
- **WHEN** the restaurateur posts generate with no effort (or `optimized`) while a cycle sandbox is open
- **THEN** the body includes a `job_id`, `status` `queued` or `running`, `search_effort` `optimized`, and `estimated_seconds`, and does not include `assignments`

#### Scenario: Effort is accepted
- **WHEN** the restaurateur posts generate with `search_effort` `minimal`
- **THEN** the job records `minimal` and `estimated_seconds` equals the engine bound for minimal

#### Scenario: Generate without cycle sandbox
- **WHEN** the restaurateur posts generate and no cycle sandbox is open
- **THEN** no job is created and the request is rejected with a French error

### Requirement: Job status is pollable
`GET` job by id SHALL return `status` as one of `queued`, `running`, `done`, or `failed`, plus `elapsed_seconds` and `estimated_seconds`. When `status` is `done`, the body MUST include the serialized engine result (assignments and warnings) produced by calling the constraint engine once. When `status` is not `done`, the body MUST NOT present a complete planning result. The system MUST NOT stream solver progress.

#### Scenario: Poll while running
- **WHEN** the restaurateur gets a job that is still running
- **THEN** `status` is `running`, `elapsed_seconds` is present, and no assignments array is returned as the result

#### Scenario: Poll when done
- **WHEN** generation has finished successfully
- **THEN** `status` is `done` and the result is the engine output written into the cycle sandbox

#### Scenario: Poll when failed
- **WHEN** generation fails
- **THEN** `status` is `failed`, a French error is present, and no fabricated planning is returned

### Requirement: Job is wrapping only; same inputs yield the same planning
The job MUST call the existing cycle generator with the sandbox draft and requested effort. It MUST NOT implement a second scorer or a different keep-best rule. The same staff, structures, hours, legal context, sandbox draft, and `search_effort` MUST produce the same assignments as a direct generator call. Jobs SHALL be stored in the live database.

#### Scenario: Deterministic wrap
- **WHEN** two generate jobs run with identical sandbox inputs and the same `search_effort`
- **THEN** the done results contain the same assignments

#### Scenario: Result lands in the sandbox
- **WHEN** a generate job reaches `done`
- **THEN** the restaurant’s cycle sandbox last result matches that job’s engine result

### Requirement: Only the restaurateur may read their jobs
A generate job SHALL belong to the session restaurant. An employee MUST NOT create or read generation jobs. A restaurateur MUST NOT read a job id that does not belong to their restaurant.

#### Scenario: Employee cannot poll generate
- **WHEN** an employee session gets a generate job id
- **THEN** the request is rejected

#### Scenario: Foreign job id
- **WHEN** a restaurateur gets a job id that is not theirs
- **THEN** the request is rejected or not found, and no other restaurant’s result is returned
