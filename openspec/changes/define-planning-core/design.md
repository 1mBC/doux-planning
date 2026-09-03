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

### 10. Generation fills post-by-post; hours-to-contract first, then nearest level

Rest pattern (who *may* work which day) stays a 14-day CP-SAT pass **with per-service coverage lower bounds**: for each open (team, service, day), enough eligible people must be reserved for that service, counting a body toward a service only if they are assigned to it. A person who already covers midi does not automatically cover evening. Reservation also respects daily/weekly hour caps from the shortest post of each covered service, so rest cannot treat a 4-hour contract as covering both midi and evening. Two consecutive rest days are **weekday pairs only** (Mon–Tue … Thu–Fri). Saturday+Sunday is not a valid consecutive pair; the solver used to pick it because Sunday is already closed — rejected, it emptied Saturday. A contract caps how many **services** a person may be reserved for that week: `floor(weekly hours / typical post length)`, where typical is the median duration of posts they can take (if that would be zero but the shortest post still fits, allow one). Closed, forced, and fully-unavailable days already count as rest. On the remaining open days, rest is pinned to the max of leftover legal rest (including a weekday pair when that preference is on) and the extra offs implied by that shift budget. A 15 h contract with ~5 h services is three shifts. “Rest almost every open day” is not a start hypothesis.

Shift fill is sequential per post window (highest required level first, then earliest start). When assigning a later post, skip a candidate who is the only person left who can cover an earlier still-empty window of the same service, if someone else can take the later post (so a 10:00 opening is not sacrificed for a 12:00 level-2). Eligible staff: same team, level ≥ post, not unavailable, no overlap, post at least as long as that employee’s min_shift_hours (default 4). Choice order: lowest hours-to-contract ratio, then already on that day, then nearest level. A shift that would exceed contractual hours is skipped when any teammate is still under hours. Unavailability remains a hard skip. A shift that would exceed that person’s weekly coupure cap is a hard skip (same as unavailability): empty post or another colleague, never a 3rd midi+soir when the cap is 2. Legal maxima (11h rest, 5h pause, daily/weekly caps) skip a candidate when another eligible person exists. Finishing a started day still applies until the coupure cap is reached.

A single greedy pass can still paint itself into a hole (someone takes midi and then cannot take evening, while a midi-only colleague was left idle). Generation therefore tries **several covering rest calendars** (legal rest, hours caps, no immediate coverage hole), fills and repairs each one, and keeps the best result (fewest empty posts, then fewest interdits, then closest contract hours, then fewest souhait, then fewest shifts below the person's role level). Breadth is a pre-calc input `search_effort`: **minimal** (16 calendars), **optimized** (default, 20× that bound, seconds), **maximal** (every covering calendar). If no covering rest calendar exists, one best-effort rest pattern is used. The output of `generate_cycle` is stable across runs for the same effort.

Avoiding **all** same-day midi+soir as a generation filter, and special-casing Saturday rest for midday-blocked staff, were tried and rejected: they overfit one restaurant file. Refusing a second service **past that person’s coupure cap** is now the rule.

Greedy highest-rank zip, exact-level-before-hours, rest-without-coverage, and “assign whoever is left even over contract” were all tried on the example restaurant file and rejected.

## Risks / Trade-offs

- [14-day solve too slow] → Default **optimized** search is 20× the minimal bound of rest calendars (seconds). **Maximal** (all covering calendars, minutes) remains available. Variables stay wave templates; still one 14-day rest model, not two independent weeks.
- [Intent taxonomy too thin] → Mitigation: start with unavailability and forced assignment; add event/extra intents later without changing the week = cycle + intents + grid shape.
- [Onboarding still long] → Mitigation: structure templates in `service-structures`; engine still runs if some days are incomplete (warnings, not crash).
- [Legal rules simplified vs convention HCR réelle] → Mitigation: treat the six listed rules as the v1 contract; keep them data displayed to the restaurateur so they can be extended without rewriting callers.
- [Reconciliation infeasible] → Mitigation: still return a best-effort proposal with couverture holes and warnings; restaurateur accepts, keeps, or edits.

## Migration Plan

Greenfield: no migration. Publish cycle from empty is “no instances yet”. The React app (and a later mobile client) must consume the FastAPI surface, not a second copy of the rules.

## Open Questions

- Fine ranking among remaining souhait criteria (evenings cap) can be tuned after generations without changing the hours-then-level rule.
- Whether linked employees can see only their own shifts or the whole team grid (does not change engine or sandbox; default until decided: own shifts).
- Job-queue library (ARQ, Celery, or FastAPI background workers) — pick at apply time; does not change specs.
