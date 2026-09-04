## Purpose

Exposes the existing domain and constraint engine over HTTP so the restaurateur can persist configuration, score and edit a sandbox, and so the employee can read published own-shifts — always by calling the engine and serializing its result.

## ADDED Requirements

### Requirement: One scoring path through the engine
HTTP evaluate, swap, rank, sandbox rescore, and generate-job completion MUST call the constraint engine and serialize its result (assignments and warnings). The adapter MUST NOT recompute warning severity, empty posts, contract hours, or candidate order in HTTP code. Optional `stats` on a serialized result MUST be counts taken from that engine result and the assignments it returned, not a second scoring model. Live adapter responses are not required to include the frozen example’s `legal_rows` / `wish_rows` tables.

#### Scenario: Evaluate is engine output
- **WHEN** the restaurateur posts the current sandbox draft to evaluate
- **THEN** the response assignments and warnings are those returned by the engine for that draft

#### Scenario: Swap is dual reassignment
- **WHEN** the restaurateur posts two shifts to swap in the sandbox
- **THEN** the response is the engine result of exchanging those two people, persisted on the sandbox

#### Scenario: Rank uses the engine per candidate
- **WHEN** the restaurateur asks who can take an empty slot
- **THEN** the response lists candidates in engine rank order, each with the engine warnings for placing that person

### Requirement: Synchronous adapters except generate
Evaluate, swap, rank, sandbox enter, sandbox edit, sandbox discard, and publish SHALL complete in the request and return the outcome in that response. They MUST NOT create a generation job. Generate remains the job-backed path.

#### Scenario: Swap is immediate
- **WHEN** the restaurateur posts a swap
- **THEN** the response includes the engine result without a `job_id`

#### Scenario: Evaluate is not a job
- **WHEN** the restaurateur posts evaluate
- **THEN** no generation job row is created

### Requirement: Sandbox HTTP follows the domain state machine
The restaurateur SHALL enter a sandbox with target `cycle` or `week` (week requires a week id). The target MUST stay immutable until discard or publish. Structural configuration writes MUST be rejected unless the sandbox target is `cycle`. Discard MUST drop the draft. Publish MUST require acknowledgement of remaining interdit warnings, then commit to the chosen target. Cycle publish MUST return dirty-week reconciliation choices (accept, keep, open-in-sandbox) without silently overwriting intent weeks. At most one sandbox per restaurant MUST be exposed.

#### Scenario: Enter week sandbox
- **WHEN** the restaurateur enters a sandbox with target week 12
- **THEN** subsequent edits and publish apply to week 12 only

#### Scenario: Structure edit needs cycle sandbox
- **WHEN** the restaurateur patches arrival waves while a week sandbox is open
- **THEN** the request is rejected with a French error

#### Scenario: Publish needs interdit acknowledgement
- **WHEN** the sandbox still has unacknowledged interdit warnings and the restaurateur publishes without those acknowledgements
- **THEN** publish is rejected and the published cycle is unchanged

#### Scenario: Publish with acknowledgements
- **WHEN** the restaurateur publishes after acknowledging remaining interdit warnings
- **THEN** the target is updated and employees no longer see the discarded draft

### Requirement: Restaurateur can persist configuration
Authenticated restaurateur routes SHALL allow reading and updating staff, structures, hours, cycle, weeks, and intents for the session restaurant. Employee sessions MUST be rejected on those writes. Updates that change coverage MUST go through the cycle sandbox as already required by cruise-planning.

#### Scenario: Restaurateur reads staff
- **WHEN** the restaurateur gets the employee list
- **THEN** the response contains that restaurant’s employees including contracts and restaurateur-owned constraints

#### Scenario: Employee cannot patch hours
- **WHEN** an employee session patches restaurant hours
- **THEN** the request is rejected and hours are unchanged

### Requirement: Employee planning route
The system SHALL expose an employee route that returns only that account’s published shifts for the session restaurant. It MUST NOT return sandbox state, other people’s shifts, or generate controls.

#### Scenario: Employee shift list
- **WHEN** a linked employee gets their planning
- **THEN** each returned shift has that employee’s id and comes from published data

### Requirement: Product errors are French
Protected and public API error bodies SHALL present a French `message` suitable to show in the product. OpenSpec requirements remain in English.

#### Scenario: French 401
- **WHEN** a protected route is called without a session
- **THEN** the error message is French
