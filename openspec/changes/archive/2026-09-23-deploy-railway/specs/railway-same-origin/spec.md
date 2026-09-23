## Purpose

Serves the FastAPI `/v1` API and the built Vite SPA from one HTTPS origin so the browser calls `/v1` without CORS, with a Railway-ready boot path.

## ADDED Requirements

### Requirement: Same-origin SPA does not swallow /v1
When a built `dist` is present, the web process SHALL serve those static files and SHALL return `index.html` for SPA paths (`/planning`, `/login`, `/register`, `/context`, `/exemple`, and `/`). Requests under `/v1` MUST keep their existing JSON API behavior. When `dist` is absent, `/v1` MUST still succeed and MUST NOT return HTTP 500 because static files are missing.

#### Scenario: Example stays 92 without dist
- **WHEN** the API is started without a `web/dist` directory
- **THEN** `GET /v1/examples/saint-cloud` is HTTP 200 with 92 assignments

#### Scenario: SPA path serves index when dist exists
- **WHEN** `web/dist/index.html` is present and a client gets `/planning`
- **THEN** the response body is that `index.html` and is not a `/v1` JSON document

#### Scenario: Dual-read without DATABASE_URL
- **WHEN** `DATABASE_URL` is unset
- **THEN** public example dual-read stays 200 / 92 and auth-backed routes stay 503

### Requirement: Railway boot uses PORT and migrates when a database URL exists
The process SHALL listen on `0.0.0.0` and `$PORT` (default `8000`). When `DATABASE_URL` is set, boot MUST run `alembic upgrade head` before serving traffic. A `postgres://` URL MUST be treated as SQLAlchemy `postgresql+psycopg://`. Tests MUST NOT call the Railway HTTP API.

#### Scenario: postgres URL is usable
- **WHEN** the environment provides `postgres://user:pass@host/db`
- **THEN** the API store connects with `postgresql+psycopg://user:pass@host/db`

#### Scenario: No database skips migrate
- **WHEN** `DATABASE_URL` is unset at boot
- **THEN** the process still serves `/v1` public dual-read routes without failing the migration step
