## Purpose

Makes PostgreSQL the live source of truth for one restaurant’s domain data, including the seeded Saint-Cloud example and France legal context, without turning data files into a second runtime.

## ADDED Requirements

### Requirement: Live store holds the onboarding context
The system SHALL persist the live company context in Postgres: identity (`name`, `invite_code`, `legal_context_id` `france`), company services, role ladders, employees (contracts, unavailabilities `{ weekday, service_id }`, Core `Wellbeing` object, `min_shift_hours`, Core `invite_token`), service types, typical week, plus accounts and sessions already specified. `GET /v1/context` and `PATCH /v1/context` MUST wrap Core `empty_restaurant` / mutators / `team_ready` / `week_label_scheme` and MUST NOT call `generate_cycle`. After a process restart (`reset_engine`), `GET /v1/context` MUST return the same body. Calendar weeks, intents, and async generation jobs remain later slices. Live `published_cycles` (salle / cuisine) and `live_sandboxes` (per-team drafts) are persisted on the company row.

#### Scenario: Empty company context after register
- **WHEN** a caller registers `kind: company` then gets `/v1/context` with that company session
- **THEN** the body has name `""`, `services` `[]`, empty ladders/types/week, `ready.salle` and `ready.cuisine` false, `legal_context_id` `france`, and `company_code` equal to the invite code

#### Scenario: Restart keeps patched context
- **WHEN** a restaurateur patches a ready salle context and the API engine is reset
- **THEN** a subsequent `GET /v1/context` returns the same name, sections, and `ready` flags

### Requirement: Staff wellbeing persists as a Core object
`staff_fiches.wellbeing` SHALL be stored as a JSON object matching Core `Wellbeing` (`consecutive_rest`, `weekend`, `max_services`, `max_coupures_per_week`). On read the adapter MUST parse an object, treat `[]` or absent as `Wellbeing()`, and reject legacy preference keys or `every_morning` / `every_evening` with HTTP 400 `Champs invalides.` Unavailabilities MUST be `{ weekday, service_id }` with both fields required. The adapter MUST NOT import or serialize `WellbeingPreference`, key lists, or `every_*` flags. No aliases.

#### Scenario: Weekend even persists and labels the restaurant
- **WHEN** a restaurateur patches a fiche `wellbeing.weekend` `even`
- **THEN** the JSONB value is the wellbeing object and a later GET returns that object with `week_labels` `parity`

#### Scenario: Empty or absent wellbeing is the Core default
- **WHEN** a fiche is stored with wellbeing `[]` or the key omitted
- **THEN** read reconstructs `Wellbeing()` and GET serializes the default object

#### Scenario: Legacy wellbeing or incomplete unavailability is rejected
- **WHEN** PATCH sends a wellbeing key list, a removed preference key, `every_morning` / `every_evening`, or an unavailability without `service_id`
- **THEN** the response is HTTP 400 `Champs invalides.` and the stored fiche is unchanged

#### Scenario: Live sandbox survives restart
- **WHEN** the restaurateur enters a live team sandbox, edits, and the API engine is reset
- **THEN** `GET /v1/live/sandbox/{team}` returns the same unpublished draft until discard or publish. Public `/v1/sandbox/*` is unchanged.

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

### Requirement: Example seed smashes the live company context
`POST /v1/context/seed-example` SHALL persist the Core `seed_example_context` result onto the session company: `services`, `hours` (JSONB), ladders, types, typical week, and example fiches with Core `invite_token`s. It MUST keep `companies.id`, `name`, `invite_code`, and `legal_context_id`. It MUST set `linked_employee_ids` to empty, `published_cycles` and `live_sandboxes` to `{ salle: null, cuisine: null }`, and MUST delete employee accounts and employee sessions for that company. It MUST overwrite already-linked fiches and MUST NOT return HTTP 409 `Cette fiche a déjà un compte.` It MUST NOT call `hydrate_delivered_cycle` or write `example_snapshots` / `data/examples/saint-cloud.json`.

#### Scenario: Seed fills an empty company from Saint-Cloud
- **WHEN** a company registers then posts `/v1/context/seed-example`
- **THEN** GET context has `ready.salle` true, `ready.cuisine` false, services midday and evening, example fiches, `week_labels` `ab`, and `GET /v1/cycles` is both null

#### Scenario: Seed again rotates tokens and stays unpublished
- **WHEN** the restaurateur seeds a second time
- **THEN** published cycles stay null and every fiche has a new Core `invite_token`

#### Scenario: Seed unlinks employees and drops their sessions
- **WHEN** a company has a linked employee and a published cycle then seeds
- **THEN** linked ids are empty, cycles are null, and the old employee Bearer is HTTP 401
