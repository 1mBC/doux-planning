## Context

See `proposal.md` for why. The engine already serializes a scored snapshot at `GET /v1/examples/saint-cloud` (`legal` + `restaurant` + `planning`). Visual form (not data source) lives in `docs/index.html` and the IDE canvas `exemple-restau-planning`. `define-planning-core` stays an active change; this slice must not archive it or edit `src/doux_planning/` except `api/` if CORS is required.

Contract shape used by the UI (do not extend):

```
GET /v1/examples/saint-cloud
  example, legal { id, rules[] }, restaurant { name, team, hours, employees[] }
  planning {
    search_effort, calendars, seconds,
    assignments[], warnings[], stats,
    legal_rows[], wish_cols[], wish_rows[]
  }
```

```
uvicorn  :8000  --  GET /v1/examples/saint-cloud
                         ^
                         | proxy /v1
vite SPA :5173  --  React read-only screen
```

## Goals / Non-Goals

**Goals:**
- Ship a Vite + React + TypeScript app under `web/` that is the restaurateur’s first useful screen.
- Keep presentation (layout, French chrome, time formatting) strictly downstream of the snapshot.

**Non-Goals:**
- Sandbox, generate, swap, publish, auth, PostgreSQL, Docker, mobile.
- New HTTP routes or a second scoring path.
- Pixel-identical clone of the GitHub Pages HTML (form, not a fork of its hardcoded numbers).
- Translating engine messages into a new diagnosis.

## Decisions

### 1. Vite proxy, no new API surface

Dev: Vite `server.proxy["/v1"]` → `http://127.0.0.1:8000`. The SPA calls `GET /v1/examples/saint-cloud` same-origin. CORS in FastAPI is unnecessary for that path; skip it unless a later verify step cannot use the proxy.

Alternative: CORS + absolute `http://localhost:8000`. Rejected for v1 — extra `api/` change for no product gain.

### 2. Presentation helpers vs forbidden logic

Allowed: index assignments by `(employee_id, day_index, service_id)`; split days 0–6 / 7–13; format minutes as `11h` / `00h`; group employees by `role.name` then list order; sum `duration_hours` already on a week sheet for the Total column; compare `post_level` to `role.level` only to show `(n)` in the cell; map known `code` to a French title while still showing `message`; map `severity` to Interdit / Couverture / Souhait.

Forbidden: recounting `stats`; deriving hours percent or wellbeing from `warnings` / `wish_rows`; displaying `hours.assigned` / `hours.contracted`; inventing `weeks_ok` / `weeks_total`; changing warning severity; filling empty posts; ranking people; calling Python.

### 3. Stats follow the JSON, not the static demo

Display `planning.stats` as returned: `hours.percent` → « Heures vs contrat »; `wellbeing.held` / `wellbeing.total` → « Souhaits bien-être » (wellbeing only, not contract). `stats.souhait` is gone. Do not reconstruct canvas KPIs or a « semaines à l’heure » counter.

### 4. Legal columns from union of row keys

`planning` has no `legal_cols`. Columns = rule ids that appear in any `legal_rows[].cells`, labels from `legal.rules[].label_fr`. Cuisine `max_daily_cuisine` stays hidden for Saint-Cloud salle because no cell uses it.

### 5. Paper-grid CSS in `web/`, desktop-first

Match the demo’s structure: sticky person column, person tint, matin/soir rows, week A then week B, then warnings, legal, wishes. Horizontal scroll on narrow widths. No UI kit required.

### 6. Types mirror the JSON

TypeScript interfaces in `web/` describe the example payload. Missing required keys → French error, empty grid.

## Risks / Trade-offs

- [Warning messages stay English] → French severity + optional French title from `code`; always keep `message`. Do not “fix” copy in the engine in this change.
- [Vite without API looks empty] → Document both processes; error state if `/v1` is down.
- [Temptation to match demo KPIs] → Spec forbids ratios absent from JSON.

## Migration Plan

Greenfield `web/`. Rollback = delete `web/` (and revert CORS if it was added). Example JSON and engine stay as they are.

## Open Questions

None that block this slice. Editing, generate, and sandbox wait for a later change that will need new routes.
