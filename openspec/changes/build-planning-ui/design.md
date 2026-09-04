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
uvicorn  :8000  --  GET /v1/examples/saint-cloud   (public)
                 --  /v1/sandbox/*                 (public)
                 --  /v1/auth/*  /v1/me  /v1/invites/{code}
                         ^
                         | proxy /v1
vite SPA :5173  --  pathname : / login, /register, /exemple
```

## Goals / Non-Goals

**Goals:**
- Keep the Vite + React + TypeScript app under `web/` as the restaurateur’s first useful screen.
- Keep presentation (layout, French chrome, time formatting) strictly downstream of the snapshot.
- Add login / register / QR / session chrome that follow `contracts/http/v1-auth.md` without scoring or inventing fields.

**Non-Goals:**
- Generate, publish, rotate invite-token UI, context panels, team wizard, colored employee grid.
- Merging `auth/infra` / `auth/core`, new FastAPI routes, a second scoring path, react-router.
- Pixel-identical clone of the GitHub Pages HTML.
- Translating engine messages into a new diagnosis.
- « Mot de passe oublié ».

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

TypeScript interfaces in `web/` describe the example payload and the auth JSON. Missing required keys → throw / French error, do not invent.

### 7. Auth screens, pathname only

No react-router: `pathname` + `URLSearchParams` + `history.pushState`.

- `/` and `/login` : un seul login (email + mot de passe) → `POST /v1/auth/login`. Le `kind` vient de `me`.
- `/register` : bascule **Entreprise** / **Salarié**. Entreprise → `{ kind: company, email, password }` seulement. Salarié → code → `GET /v1/invites/{company_code}` → choisir une fiche (`id`, `name`, `role`, `team`) → `{ kind: employee, company_code, employee_id, email, password }` (pas de token).
- QR : `/register?company_code=…&employee_token=…` — kind salarié verrouillé, pas de liste, POST avec `employee_token` (pas d’`employee_id`).
- Password ≥ 8. Afficher `detail` tel quel. Pas de « mot de passe oublié ».
- Token : `sessionStorage`. Bearer seulement sur register/login/logout/`GET /v1/me`. Jamais sur `/v1/examples/*` ni `/v1/sandbox/*`.
- Reload : si token, `GET /v1/me` ; 401 → login + oublier le token. 503 (`Base indisponible.`) n’empêche pas l’exemple.
- Session chrome : email + kind (Entreprise / Salarié) + **Déconnexion** (`POST /v1/auth/logout`, oublier le token).
- Sans session : login/register **et** `/exemple` (lien « Voir l’exemple »). La grille n’est pas derrière le login.
- `kind: employee` : pas de Mode édition ; « Le planning publié personnel arrive plus tard. »
- `kind: company` (et sans session) : grille + sandbox comme aujourd’hui.

Hors slice : rotate invite-token, panneaux contexte, wizard, generate.

## Risks / Trade-offs

- [Warning messages stay English] → French severity + optional French title from `code`; always keep `message`. Do not “fix” copy in the engine in this change.
- [Vite without API looks empty] → Document both processes; error state if `/v1` is down.
- [Temptation to match demo KPIs] → Spec forbids ratios absent from JSON.

## Migration Plan

Greenfield `web/`. Rollback = delete `web/` (and revert CORS if it was added). Example JSON and engine stay as they are.

## Open Questions

None that block this slice. Rotate invite-token and context panels wait.
