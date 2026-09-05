## Context

See `proposal.md`. `contracts/deploy/railway.md` is frozen. Today the repo has a single-stage Python `Dockerfile` (uvicorn port 8000, always `alembic upgrade head`) and `.dockerignore` excludes `web/`. Local Compose (db + api, Bastien ports) must not change. FastAPI already exposes `/v1/*` with dual-read when `DATABASE_URL` is missing.

## Goals / Non-Goals

**Goals:**
- One image: Vite `web/dist` + FastAPI, Railway Dockerfile builder.
- SPA fallback that never captures `/v1`.
- Boot: `$PORT`, optional Alembic, `postgres://` normalize in `api/`.

**Non-Goals:**
- Editing `web/src/`, `contracts/`, engine formulas, Compose ports.
- GitHub Actions, Railway tokens in the repo, CORS, a second front service.

## Decisions

### 1. Multi-stage Dockerfile, `web/` allowed in the build context

Stage 1: Node builds `web/` (`npm ci` + `npm run build`). Stage 2: existing Python 3.12-slim install, copy `web/dist` to `/app/web/dist`. Stop and surface if the Vite build requires `web/src/` edits.

Alternative: two Railway services. Rejected — freeze is one origin.

### 2. Static + catch-all after `/v1` routes

If `web/dist/index.html` exists (repo root or `/app/web/dist`), mount assets and return `index.html` for `/` and non-`/v1` GET paths. If absent, register nothing — TestClient `/v1` unchanged.

### 3. Normalize in `database_url()`; Alembic calls that helper

`postgres://` → `postgresql+psycopg://`. Also accept `postgresql://` without a driver (Railway plugin default) by rewriting to `postgresql+psycopg://`. `alembic/env.py` reads `doux_planning.api.db.database_url()` so migrate and the app share one adapter. Logic stays in `api/`.

### 4. Entrypoint: migrate only when `DATABASE_URL` is set

`CMD` runs `alembic upgrade head` then `uvicorn --host 0.0.0.0 --port ${PORT:-8000}` only if `DATABASE_URL` is set. Lifespan seed stays as today.

### 5. `railway.toml` is builder-only

```
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"
```

No startCommand, no invented env. Auto-deploy to `master` is Bastien’s click.

## Risks / Trade-offs

- [Vite build needs a `web/src` change] → Stop and report; do not edit `web/src/`.
- [Catch-all registered too early] → Register SPA routes last; refuse paths that start with `v1`.
- [Alembic sees raw `postgres://`] → Share `database_url()` from `api/`.

## Migration Plan

Merge `deploy/infra` to `master`. Bastien links Railway to `master`, adds Postgres, checks `DATABASE_URL`. Rollback: previous image; local Compose unchanged.

## Open Questions

None.
