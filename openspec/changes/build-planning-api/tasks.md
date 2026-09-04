## 1. Example contract and seed

- [x] 1.1 Add PostgreSQL 16 + Alembic + SQLAlchemy 2 + psycopg to the API stack (`pyproject.toml`, `docker-compose.yml` with `db` / `api`), and verify `docker compose up` reaches a healthy Postgres and the API process starts with `DATABASE_URL`
- [x] 1.2 Create migrations for `legal_contexts`, `restaurants` (`legal_context` id, no copied `legal_rules`), and `example_snapshots` (frozen `planning` jsonb), and verify `alembic upgrade head` succeeds on an empty database
- [x] 1.3 Seed France from `data/legal/france.json` and Saint-Cloud from `data/examples/saint-cloud.json` at boot or migrate, and verify the restaurant row stores `legal_context = france` with no `legal_rules` column/document
- [x] 1.4 Point `GET /v1/examples/{example_id}` at the live store (not a per-request file read, not `generate_cycle`, not a job) inside `src/doux_planning/api/` only, and verify `TestClient` `GET /v1/examples/saint-cloud` is 200 with `example`, `legal.id == france`, `legal.kind == legal_context`, no `restaurant.legal_rules`, `planning.search_effort == optimized`, `planning.stats.assignments == 70`, and `GET /v1/examples/inconnu` is 404 (extend `tests/test_planning.py`)

## 2. Auth for restaurateur and employee

- [ ] 2.1 Add Argon2 password hashes plus `restaurateur_accounts`, `employee_accounts`, and `sessions` tables (opaque Bearer token), and verify a stored password is hashed and the raw token is not persisted
- [ ] 2.2 Implement `POST /v1/auth/restaurateur/register` (first account only, bound to the seeded restaurant) and `POST /v1/auth/restaurateur/login`, and verify register-then-login issues a session, a second register is rejected, and a wrong password is rejected with a French error (extend existing tests)
- [ ] 2.3 Implement `GET /v1/invites/{code}` (restaurant name + unlinked employees) and `POST /v1/auth/employee/register` `{invite_code, employee_id, email, password}` using existing `redeem_invite`, and verify a valid code links the account, an invalid code is rejected, and a second register on the same employee id is rejected
- [ ] 2.4 Implement employee login, `GET /v1/me`, and `POST /v1/auth/logout`, and verify protected routes without a session return a French error, the session `restaurant_id` is used (no restaurant id in the path), and logout invalidates the token

## 3. Domain persistence

- [ ] 3.1 Persist staff, structures, hours, invite code, published cycle, weeks, intents, and at most one sandbox per restaurant in Postgres (still only new code under `api/` plus migrations), and verify a process restart returns the same published cycle without calling generate
- [ ] 3.2 Wire a Postgres-backed store that performs `PlanningStore` operations without editing `planning.py` / `engine.py`, and verify in-memory `PlanningStore` domain tests still pass unchanged
- [ ] 3.3 Verify a restaurateur live staff edit does not rewrite `data/examples/saint-cloud.json`, and that writing a different live cycle/sandbox does not change `GET /v1/examples/saint-cloud`

## 4. Generation jobs

- [ ] 4.1 Add a `jobs` table and `POST /v1/generate` that inserts `queued` and returns `job_id`, `status`, `search_effort` (default `optimized`), and `estimated_seconds` from engine `SEARCH_SECONDS`, and verify the response has no `assignments` and that generate without a cycle sandbox is rejected with a French error
- [ ] 4.2 Add a Compose `worker` that claims jobs with `FOR UPDATE SKIP LOCKED`, calls `generate_cycle` with the sandbox draft and effort, writes the sandbox, and sets `done` or `failed`, and verify `GET /v1/jobs/{id}` reports `queued|running|done|failed`, `elapsed_seconds`, `estimated_seconds`, result only when `done`, and French error with no fake planning when `failed`
- [ ] 4.3 Verify two generate jobs with the same sandbox inputs and effort return the same assignments, that an employee cannot create or poll jobs, and that a foreign `job_id` does not leak another restaurant’s result

## 5. Synchronous adapters

- [ ] 5.1 Add restaurateur `POST /v1/evaluate`, `/v1/swap`, `/v1/rank` that call the engine and serialize `EngineResult` (no job row), and verify swap/rank/evaluate warnings match a direct engine call on the same draft
- [ ] 5.2 Add sandbox enter (target `cycle` or `week`), edit, discard, and publish with interdit acknowledgements, and verify week-target publish does not mutate the cycle, structure edits are rejected on a week sandbox, unacked interdit blocks publish, and cycle publish returns dirty-week reconciliation options
- [ ] 5.3 Add restaurateur reads/writes for staff, structures, hours, cycle, and weeks, plus `GET /v1/me/shifts` for the employee, and verify the employee sees only own published shifts (not sandbox, not the team grid) and is rejected on generate/sandbox/config writes with a French error
