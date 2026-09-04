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

### Requirement: Live sandbox HTTP wraps Core per team
The restaurateur SHALL edit a published team cycle through `/v1/live/sandbox/{team}` (Bearer company). Routes MUST wrap Core `enter_live_sandbox`, preview / apply / undo (same proposal shapes as the public joujou), `discard_live_sandbox`, and `publish_live_sandbox`. `team` is `salle` or `cuisine`. `NoPublishedCycle` MUST be HTTP 409 `Aucun cycle publié pour cette équipe.` Discard MUST re-enter the current published cycle (empty history). Publish MUST write only that team’s `published_cycles` key, close the draft (`GET` live → 404), and leave the other team intact. Public `/v1/sandbox/*` MUST stay unauthenticated and unchanged. Week reconciliation, evaluate / swap / rank, and `/me/shifts` remain later slices.

#### Scenario: Enter salle after generate
- **WHEN** salle has a published cycle and the restaurateur posts enter for `salle`
- **THEN** the response is HTTP 200 `LiveState` with `"team": "salle"` and the published assignments

#### Scenario: Enter cuisine without a published cycle
- **WHEN** only salle is published and the restaurateur posts enter for `cuisine`
- **THEN** the response is HTTP 409 French and no cuisine draft is stored

#### Scenario: Discard restores published
- **WHEN** the restaurateur retunes, commits, then discards
- **THEN** a subsequent enter matches the published assignments with empty history

#### Scenario: Publish updates cycles only
- **WHEN** the restaurateur publishes a retuned salle draft
- **THEN** `GET /v1/cycles` shows the new salle cycle, `cuisine` stays `null`, and `GET /v1/live/sandbox/salle` is 404

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
