## Context

Greenfield repo. See `proposal.md` for motivation. Stack is chosen: Python for the API and constraint engine (OR-Tools), React for the web client, PostgreSQL, Docker Compose. The engine stays a pure module behind the HTTP API so a future mobile app can reuse it.

Human-scale restaurant: one establishment, one restaurateur, on the order of 15–25 employees, two teams.

## Goals / Non-Goals

**Goals:**
- Separate a pure constraint engine from UI and persistence.
- Make cycle, calendar instance, intents, and sandbox first-class data, not an afterthought of a grid widget.
- Keep generation, validation, suggestion, and swap on one scoring path.

**Non-Goals:**
- Building the React UI or mobile clients in this change (API-first; web is the next slice).
- Employee-authored constraints, notifications, extras staffing, native apps, multi-restaurant groups.
- Pixel-level UI. Shared-hosting PHP deploy (incompatible with OR-Tools).

## Decisions

### 1. Engine as a pure module

The engine is a function of (staff, structures, legal rules, cycle-or-week draft) → (assignments, warnings, optional candidate ranking). UI, HTTP, and database do not sit inside scoring.

Alternatives considered: scoring in UI event handlers; separate “generator” and “validator” services. Rejected because they drift (see spec: one engine).

### 2. Posts, not cumulative headcount

Each wave defines exclusive posts. Matching is min-cost assignment per shift: cost 0 for exact level, then +1 per extra level of overqualification; leaving a higher post empty to fill a lower one is prohibitive. Role is frozen for the whole shift.

Alternative: cumulative “N people ≥ level 2” including the chef in the commis count. Rejected by product (chef work is a distinct post).

### 3. Cycle is 14 days with wrap-around; instances are projections

Source of truth for cruise mode is the 14-day cycle. Calendar weeks are instances: copy of the cycle plus intents. Generation solves 14 days in one run (optionally decomposed as rest-pattern then shifts if a later solver spike needs it). Sequential week-A-then-week-B generation is not used.

Alternative: weekly solver + stitch. Rejected: myopic on every-other-weekend and B→A wrap.

### 4. Intents, not only grid diffs

A dirty week stores intents (unavailability, forced assignment, etc.) plus the published grid. Cycle republish re-solves `new cycle + intents` and asks for validation. Without intents, reconciliation cannot be defined.

### 5. Sandbox is a persisted working copy with target chosen at entry

One sandbox per restaurant. Target is `cycle` | `calendar-week-id` at entry, immutable until discard or publish. Structural config that changes coverage is a cycle-sandbox edit. Live rescoring after each mutation; employees only see published data.

Alternative: choose ponctuel vs croisière per gesture, or at publish. Rejected: mixed drafts cannot be merged cleanly.

### 6. Fifteen-minute evaluation, wave-based decisions

Coverage is checked on 15-minute slices. Search variables are feasible `[start, end, post]` templates induced by waves, not 96 slots × employees × 14 days.

### 7. Warnings are data, publish is never a hard block

Three severities travel with the draft and remain on the published planning if acknowledged. The engine never throws to prevent an override; the UI requires acknowledgement of remaining warnings at publish.

### 8. Python API + React web, mobile later on the same API

- **API, domain, engine:** Python 3.12, FastAPI, OR-Tools (CP-SAT). Generation runs asynchronously (job queue) so the UI does not block on a 14-day solve.
- **Data:** PostgreSQL.
- **Web v1:** React + TypeScript (Vite), desktop-responsive SPA talking only to the API.
- **Deploy:** Docker Compose on a VPS (e.g. Coolify / Dokploy).
- **Mobile later:** same HTTP API; React Native or Flutter chosen when that slice starts.

PHP/Laravel as the system of record was rejected: easy shared hosting does not host a serious rostering solver, and a Laravel app plus a Python worker is two runtimes for no gain. HTML-only server rendering was rejected so a future app does not force a rewrite.

First implementation of this change remains the domain model + engine + sandbox state machine with tests, in Python. The React shell is a follow-up change.

### 9. Engine stays out of the HTTP layer

FastAPI adapters map HTTP to the pure engine module (decision 1). Scoring is never implemented in React.

## Risks / Trade-offs

- [14-day solve too slow] → Mitigation: keep variables as wave templates; decompose rest-pattern then shifts; still one 14-day model, not two independent weeks.
- [Intent taxonomy too thin] → Mitigation: start with unavailability and forced assignment; add event/extra intents later without changing the week = cycle + intents + grid shape.
- [Onboarding still long] → Mitigation: structure templates in `service-structures`; engine still runs if some days are incomplete (warnings, not crash).
- [Legal rules simplified vs convention HCR réelle] → Mitigation: treat the six listed rules as the v1 contract; keep them data displayed to the restaurateur so they can be extended without rewriting callers.
- [Reconciliation infeasible] → Mitigation: still return a best-effort proposal with couverture holes and warnings; restaurateur accepts, keeps, or edits.

## Migration Plan

Greenfield: no migration. Publish cycle from empty is “no instances yet”. The React app (and a later mobile client) must consume the FastAPI surface, not a second copy of the rules.

## Open Questions

- Exact ranking weights among souhait criteria (can be tuned after first generations without changing specs).
- Whether linked employees can see only their own shifts or the whole team grid (does not change engine or sandbox; default until decided: own shifts).
- Job-queue library (ARQ, Celery, or FastAPI background workers) — pick at apply time; does not change specs.
