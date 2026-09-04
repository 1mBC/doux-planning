## 1. Example contract and seed

- [x] 1.1 Add PostgreSQL 16 + Alembic + SQLAlchemy 2 + psycopg to the API stack (`pyproject.toml`, `docker-compose.yml` with `db` / `api`), and verify `docker compose up` reaches a healthy Postgres and the API process starts with `DATABASE_URL`
- [x] 1.2 Create migrations for `legal_contexts`, `restaurants` (`legal_context` id, no copied `legal_rules`), and `example_snapshots` (frozen `planning` jsonb), and verify `alembic upgrade head` succeeds on an empty database
- [x] 1.3 Seed France from `data/legal/france.json` and Saint-Cloud from `data/examples/saint-cloud.json` at boot or migrate, and verify the restaurant row stores `legal_context = france` with no `legal_rules` column/document
- [x] 1.4 Point `GET /v1/examples/{example_id}` at the live store (not a per-request file read, not `generate_cycle`, not a job) inside `src/doux_planning/api/` only, and verify `TestClient` `GET /v1/examples/saint-cloud` is 200 with `example`, `legal.id == france`, `legal.kind == legal_context`, no `restaurant.legal_rules`, `planning.search_effort == optimized`, `planning.stats.assignments == 70`, and `GET /v1/examples/inconnu` is 404 (extend `tests/test_planning.py`)

## 2. Auth HTTP (unified contract)

- [x] 2.1 Add Argon2 password hashes plus live company/fiche tables, `restaurateur_accounts`, `employee_accounts`, and hashed `sessions` (opaque Bearer), and verify a stored password is hashed, the raw token is not persisted, and auth without `DATABASE_URL` returns 503 while the public example dual-read is unchanged
- [x] 2.2 Implement unified `POST /v1/auth/register` and `POST /v1/auth/login` (`kind: company` creates a new empty company, not Saint-Cloud; `kind: employee` wraps `redeem_invite`). Verify company register → login → `GET /v1/me` `kind` company, duplicate email is 409, wrong password is 401, and `/v1/auth/restaurateur/*` + `/v1/auth/employee/*` are not implemented (extend TestClient tests)
- [x] 2.3 Implement public `GET /v1/invites/{company_code}` (unlinked fiches only, no tokens in JSON) and `POST /v1/staff/{id}/invite-token` (company Bearer, `rotate_employee_invite_token`). Verify two inserted fiches appear in invites, manual register on A is 201 then gone from invites, same fiche is 409, QR token B links B, bad `company_code` is 400, and rotate A rejects the old token then accepts the new one
- [x] 2.4 Implement `POST /v1/auth/logout` and `GET /v1/me`, and verify logout then `/me` is 401, `GET /v1/examples/saint-cloud` stays 200 / 92 assignments with and without a session, and existing sandbox routes stay 200 without Bearer

## 3. Live context persist (`GET` / `PATCH /v1/context`)

- [x] 3.1 Extend `companies` / `staff_fiches` (legal_context_id, services, ladders, types, typical week, contract / unavail / wellbeing / min_shift / role level) and implement `GET /v1/context` (Bearer company, wrap `empty_restaurant` / `team_ready`, no `generate_cycle`). Verify register company then GET is empty (name `""`, services `[]`, ladders/types/week empty, ready false, `legal_context_id` `france`, `company_code` = invite), employee Bearer is 403, and without `DATABASE_URL` context is 503
- [x] 3.2 Implement `PATCH /v1/context` (optional section replace) and persist restart-safe. Verify PATCH name + salle ladder + 1 fiche + services + type + open week → `ready.salle` true / `ready.cuisine` false; `reset_engine` then same GET; open cell without type → salle false; new fiches get a Core `invite_token`; rotate stays `POST /v1/staff/{id}/invite-token`
- [x] 3.3 Verify PATCH does not write `example_snapshots` or `data/examples/saint-cloud.json`, `GET /v1/examples/saint-cloud` stays 92 assignments, `GET /v1/invites/{company_code}` lists the unlinked fiche, and auth login/logout stay green

## 4. Generation jobs

- [ ] 4.1 Add a `jobs` table and `POST /v1/generate` that inserts `queued` and returns `job_id`, `status`, `search_effort` (default `optimized`), and `estimated_seconds` from engine `SEARCH_SECONDS`, and verify the response has no `assignments` and that generate without a cycle sandbox is rejected with a French error
- [ ] 4.2 Add a Compose `worker` that claims jobs with `FOR UPDATE SKIP LOCKED`, calls `generate_cycle` with the sandbox draft and effort, writes the sandbox, and sets `done` or `failed`, and verify `GET /v1/jobs/{id}` reports `queued|running|done|failed`, `elapsed_seconds`, `estimated_seconds`, result only when `done`, and French error with no fake planning when `failed`
- [ ] 4.3 Verify two generate jobs with the same sandbox inputs and effort return the same assignments, that an employee cannot create or poll jobs, and that a foreign `job_id` does not leak another restaurant’s result

## 5. Synchronous adapters

- [ ] 5.1 Add restaurateur `POST /v1/evaluate`, `/v1/swap`, `/v1/rank` that call the engine and serialize `EngineResult` (no job row), and verify swap/rank/evaluate warnings match a direct engine call on the same draft
- [ ] 5.2 Add sandbox enter (target `cycle` or `week`), edit, discard, and publish with interdit acknowledgements, and verify week-target publish does not mutate the cycle, structure edits are rejected on a week sandbox, unacked interdit blocks publish, and cycle publish returns dirty-week reconciliation options
- [ ] 5.3 Add restaurateur reads/writes for staff, structures, hours, cycle, and weeks, plus `GET /v1/me/shifts` for the employee, and verify the employee sees only own published shifts (not sandbox, not the team grid) and is rejected on generate/sandbox/config writes with a French error
