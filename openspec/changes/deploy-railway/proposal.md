## Why

The product needs one HTTPS origin on Railway that follows `master`, so the Vite SPA and FastAPI `/v1` share the same host. Local Compose stays as-is; preview-per-branch and a sleeping free web host are out.

## What Changes

- Multi-stage Dockerfile: `npm run build` in `web/` then copy `dist` into the API image.
- FastAPI serves `web/dist` plus SPA fallback (`/planning`, `/login`, `/register`, `/context`, `/exemple`) without swallowing `/v1`.
- Process listens on `0.0.0.0:$PORT` (default 8000). `alembic upgrade head` at boot when `DATABASE_URL` is set.
- Normalize Railway `postgres://` to `postgresql+psycopg://` inside `api/` only.
- `railway.toml` names the Dockerfile builder. No GitHub Action, no Railway API calls in tests.
- Without `dist`, TestClient `/v1` stays unchanged (no 500). Local Compose ports stay Bastien’s.

## Capabilities

### New Capabilities

- `railway-same-origin`: one Docker image serves FastAPI `/v1` and the built SPA from the same origin, with deploy boot (`PORT`, Alembic, `DATABASE_URL` normalize).

### Modified Capabilities

- (none — public `/v1` JSON contracts stay the same)

## Impact

- `Dockerfile` (multi-stage), `.dockerignore` (must allow `web/` for the image build), `railway.toml`, `src/doux_planning/api/` (static SPA, `database_url` normalize, boot migrate).
- Tests: TestClient `/v1` without dist; optional SPA `/planning` skip if `dist` absent; existing pytest stays green.
- Do not edit `web/src/`, `contracts/`, engine formulas, or Compose ports. No archive / sync of other changes.
