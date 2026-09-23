# Proposal

## Why

The admin historique table only lists generate emails and restaurants. An operator cannot see the note of that generate, open the restaurant’s current planning, or copy a one-shot login link for a private window. File 70 (`contracts/domain/admin-historique.md`) freezes those three gestures for Infra + UI.

## What Changes

- Persist `generate_logs.restaurant_id` (nullable, no FK) and `generate_logs.score_global` (nullable). Backfill `restaurant_id` from restaurateur emails (lowercase). New writes store both.
- `GET /v1/admin/generates` always emits `restaurant_id` and `score_global` (null on old rows).
- Admin read-only views of a restaurant’s live planning: `GET /v1/admin/restaurants/{restaurant_id}/cycles` and `/context` return the same JSON as the company GET routes. 404 `Restaurant introuvable.`
- Copyable impersonate link: `POST /v1/admin/impersonate` mints a 15-minute one-shot token; public `POST /v1/auth/impersonate` consumes it into a company session (`SESSION_TTL` 30 d) without touching other sessions.
- SPA FastAPI serves `/impersonate/{token}` and `/admin/planning/{restaurant_id}` as `index.html`.
- Alembic after `20260921_0016`: the two log columns plus table `impersonate_tokens`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `build-planning-api`: generate log fields, admin cycles/context, impersonate mint and consume, SPA fallback routes.

## Impact

- `src/doux_planning/api/` (`app.py`, `auth.py`, `generate.py`, `context.py`, `db.py`) and Alembic.
- TestClient tests (`skipif` without `DATABASE_URL`).
- Do not edit `web/`, Core outside `api/`, `contracts/`, `engine.py` formulas, or `data/bench/`. Files 71–72 (bench import, delete/tombstone) stay out of scope.
