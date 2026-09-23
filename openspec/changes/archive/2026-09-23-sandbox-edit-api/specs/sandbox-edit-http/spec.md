## Purpose

Exposes HTTP enter, preview, commit, and undo for the Saint-Cloud cycle sandbox by wrapping the existing Python preview store, without scoring in the adapter and without changing the public example snapshot.

## ADDED Requirements

### Requirement: Enter hydrates Saint-Cloud and opens or reuses the cycle sandbox
`POST /v1/sandbox/enter` SHALL hydrate Saint-Cloud into the store when it is not already loaded, then open a cycle-target sandbox. If a sandbox already exists, the system MUST reuse it (same as `enter_sandbox`). The response MUST be HTTP 200 with the sandbox state, including `score` of the open draft. The request MUST NOT require authentication, MUST NOT accept a week vs cycle choice, MUST NOT call `generate_cycle`, and MUST NOT rewrite `data/examples/saint-cloud.json`.

#### Scenario: First enter
- **WHEN** no sandbox is loaded and a client posts enter
- **THEN** the response is 200 with `sandbox.target` `cycle`, `history` `[]`, `history_length` 0, a `score` object, Saint-Cloud restaurant employees, and planning assignments plus warnings from the hydrated cycle

#### Scenario: Re-enter reuses
- **WHEN** a sandbox already exists and a client posts enter again
- **THEN** the same draft, history, and score are returned, not a discarded reset

### Requirement: GET sandbox returns current state or a French 404
`GET /v1/sandbox` SHALL return the same state shape as enter when a sandbox is open. If none is open, it MUST return HTTP 404 with a French error. No authentication is used in this change (404, not 401).

#### Scenario: Get after enter
- **WHEN** enter has succeeded and a client gets `/v1/sandbox`
- **THEN** the body matches the current draft assignments, history length, and score

#### Scenario: Get without enter
- **WHEN** no sandbox is open
- **THEN** the response is 404 with a French message and no planning body

### Requirement: Preview calls Python only and does not mutate
`POST /v1/sandbox/preview` SHALL call only the matching Python preview and MUST NOT change the draft or history. Replace and swap take `{ gesture, shift }` and return `{ "proposals": [ … ] }` ordered by increasing `rank`. Retune MUST include `start_minutes` and `end_minutes` and returns 0 or 1 proposal. Fill MUST take `{ gesture, slot, start_minutes, end_minutes }` where `slot` is row identity without `post_level` or hours; both hours null or omitted call `preview_fill` with `None, None`; both numbers are passed through; exactly one set MUST be 400 French. A proposal MUST include `rank`, `gesture`, `start_minutes`, `end_minutes`, `employee_id`, `partner`, `impact`, `current_score`, and `trial_score`. It MUST NOT include `assignments`, `delta`, or trial-wide `warnings`. `partner` MUST include Shift identity fields including `day_index` and `weekday`. A shift absent from the draft MUST yield 404 or 400 with a French error. Identical retune hours MUST yield 400 French. Duration below the employee minimum MUST yield 400 French. An occupied fill cell MUST yield 409 French. A closed service MUST yield 400 French.

#### Scenario: Preview retune does not crant
- **WHEN** the restaurateur previews retune on an existing shift with new start and end
- **THEN** at most one proposal is returned, GET still has the same assignments and `history_length` 0, and the proposal has `impact` plus scores without `delta`

#### Scenario: Identity retune is rejected
- **WHEN** preview retune uses the shift’s current start and end
- **THEN** the response is 400 French and the draft is unchanged

#### Scenario: Unknown shift
- **WHEN** preview is posted with a shift that is not in the draft
- **THEN** the request is rejected with a French 404 or 400

#### Scenario: Replace role_fit follows the engine
- **WHEN** the restaurateur previews replace on a Saint-Cloud shift
- **THEN** each proposal includes `impact.role_fit` as a list of 0 or 1 object with `current_gap`, `trial_gap`, and `kind` `better` or `worse`, matching the Python impact (empty when the engine omits a row)

#### Scenario: Fill empty Emma Monday midday
- **WHEN** the restaurateur previews fill on Emma Monday midday with null hours
- **THEN** the response is 200, rank 1 is emma with start 600 and end 960, `role_fit` is empty, and the draft is unchanged

#### Scenario: Fill occupied cell
- **WHEN** that cell already has an assignment and the client previews fill
- **THEN** the response is 409 French

### Requirement: Commit replays preview and applies the matching proposal
`POST /v1/sandbox/commit` SHALL replay the corresponding preview then call `apply_proposal`. Retune MUST pass the posted `start_minutes` and `end_minutes` into that preview (0 or 1 proposal). Replace matches `employee_id`; swap matches partner shift equality; fill matches `employee_id` after replaying `preview_fill` with the posted slot and hours. Extra fields for other gestures MUST be ignored. Missing fields for the chosen gesture MUST be 400 French. The 200 body is the sandbox state after the cran, with `history` appending a recap `{ index, gesture, shift, slot, employee_id, start_minutes, end_minutes, partner, impact }` (1 = oldest). Occupied commits set `shift` from the body and `slot` null; fill sets `slot` from the body and `shift` null. Hours, partner, employee_id, and impact MUST come from the chosen proposal. The system MUST NOT invent a volatile `proposal_id`.

#### Scenario: Commit retune
- **WHEN** the client commits retune with chosen start and end
- **THEN** the draft assignments match that trial and history has one recap with gesture `retune`, the source `shift`, null `slot`, and the proposal `impact`

#### Scenario: Commit fill
- **WHEN** the client commits fill for Emma Monday midday with the previewed hours
- **THEN** the draft contains that shift, history has one recap with gesture `fill` and the source `slot`, and `GET /v1/examples/saint-cloud` still has 92 assignments

#### Scenario: Commit missing fields
- **WHEN** gesture is `replace` and `employee_id` is omitted
- **THEN** the response is 400 French and the draft is unchanged

### Requirement: Undo pops one cran
`POST /v1/sandbox/undo` SHALL call `undo_sandbox` (last cran only) and return the state after undo. An empty history MUST be HTTP 409 with a French message (`EmptyHistoryError`).

#### Scenario: Undo after one commit
- **WHEN** one cran exists and the client posts undo
- **THEN** assignments return to the pre-cran draft and `history` is empty

#### Scenario: Undo empty
- **WHEN** history is empty and the client posts undo
- **THEN** the response is 409 French and the draft is unchanged

### Requirement: Discard resets the sandbox to the hydrated cycle
`POST /v1/sandbox/discard` SHALL call `discard_sandbox`, clear history recaps, then `enter_sandbox` with target `cycle`. The 200 body is the sandbox state with empty history and the hydrated cycle assignments. If no sandbox is open, the response MUST be 404 French. The public example snapshot MUST NOT change. When `DATABASE_URL` is set, the persisted session MUST be deleted then rewritten with the fresh draft.

#### Scenario: Discard after a cran
- **WHEN** a cran exists and the client posts discard
- **THEN** history is empty, assignments match the pre-cran hydrated cycle, and `GET /v1/examples/saint-cloud` still has 92 assignments

#### Scenario: Discard without enter
- **WHEN** no sandbox is open
- **THEN** the response is 404 French

### Requirement: Live planning is not the example snapshot
Sandbox state `planning` SHALL contain `assignments` and `warnings` only (with `duration_hours` on each shift). It MUST NOT include example-snapshot `legal_rows`, `wish_rows`, or `stats`. `GET /v1/examples/saint-cloud` MUST keep its frozen 200.

#### Scenario: Example route unchanged after sandbox edit
- **WHEN** a retune is committed in the sandbox
- **THEN** `GET /v1/examples/saint-cloud` still returns the frozen snapshot assignments count

### Requirement: Persist sandbox when DATABASE_URL is set
When `DATABASE_URL` is set, draft, engine history, and API history recaps MUST survive an API process restart. When it is absent, in-memory process state is sufficient. Postgres MUST NOT become required for the public example route.

#### Scenario: Restart with database
- **WHEN** a cran exists, `DATABASE_URL` is set, and the API process restarts
- **THEN** GET sandbox still shows that cran and draft
