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
                 --  GET|PATCH /v1/context   (Bearer company)
                 --  POST /v1/generate  GET /v1/cycles  (Bearer company)
                 --  /v1/live/sandbox/{team}/*  (Bearer company)
                         ^
                         | proxy /v1
vite SPA :5173  --  pathname : / login, /register, /exemple, /context, /planning
```

## Goals / Non-Goals

**Goals:**
- Keep the Vite + React + TypeScript app under `web/` as the restaurateur’s first useful screen.
- Keep presentation (layout, French chrome, time formatting) strictly downstream of the snapshot.
- Add login / register / QR / session chrome that follow `contracts/http/v1-auth.md` without scoring or inventing fields.
- Company wizard at `/context` following `contracts/http/v1-context.md`.
- Company published cycle at `/planning` following `contracts/http/v1-generate.md` (`search_effort: "minimal"`).
- Live sandbox Mode édition on `/planning` following `contracts/http/v1-live-sandbox.md` (shapes from `v1-sandbox-edit.md`).

**Non-Goals:**
- `optimized` / `maximal` UI, changing the public `/v1/sandbox/*` joujou, rotate invite-token, colored employee grid.
- Merging `live/infra` / `live/core`, new FastAPI routes, a second scoring path, react-router.
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
- Token : `sessionStorage`. Bearer sur register/login/logout/`GET /v1/me`, GET/PATCH `/v1/context`, `POST /v1/generate`, `GET /v1/cycles`, `/v1/live/sandbox/{team}/*`. Jamais sur `/v1/examples/*` ni `/v1/sandbox/*`.
- Reload : si token, `GET /v1/me` ; 401 → login + oublier le token. 503 n’empêche pas l’exemple.
- Session chrome : email + kind + **Déconnexion**. Company : lien **Mon restaurant** → `/context` ; lien **Planning** → `/planning`.
- Sans session : login/register **et** `/exemple`. La grille n’est pas derrière le login.
- `kind: employee` : pas de Mode édition ; pas de wizard ; pas de `/planning` ; « Le planning publié personnel arrive plus tard. »
- `kind: company` : wizard `/context` + `/planning` + grille / sandbox exemple.

### 8. Context wizard (company)

Séquentiel puis tout éditable. Salle et cuisine indépendantes.

1. Rôles (équipe) : nom + niveau ≥ 1. Afficher : un niveau plus élevé peut tenir un poste inférieur. PATCH `ladders` avec `substitution_explained: true` (les deux équipes).
2. Fiches (équipe) : nom, rôle de l’échelle, heures contrat, indispos, wellbeing (clés contrat), `min_shift_hours` 4. PATCH `employees` = liste complète. Afficher `invite_token` + URL register QR. Pas de rotate.
3. Services (resto, une fois) : petit-déj / déj / dîner → `morning` / `midday` / `evening`. PATCH `services`.
4. Types (équipe × service) : nom, vagues ±15, `post_levels`. PATCH `types` = liste complète.
5. Semaine type : type ou Fermé. PATCH `typical_week` = `{ salle, cuisine }`. Fermé : `closed: true`, `type_id` null.

Identité : PATCH `name` (`""` OK). « Droit du travail : France » lecture seule (`legal_context_id`). Afficher `company_code`.  
`ready.salle` / `ready.cuisine` = JSON seulement, badges « Prêt à calculer » / « Pas encore prêt ».

### 9. Published cycle (company)

Route `/planning`. Au load : `GET /v1/cycles` + `GET /v1/context`. Sélecteur Salle / Cuisine. **Calculer** actif seulement si `ready[team] === true` (badge context). Sinon disabled, pas de POST. POST `{ team, search_effort: "minimal" }`. Busy + `detail` si 409/400. Si `published[team]` non null : grille 14 j. (A/B) fiches de l’équipe + assignments + warnings (message moteur, sévérité FR). Pas de stats / legal_rows / wish_rows inventés. Cuisine `null` : « Pas encore calculé », salle intacte. Reload = même GET. Recalculer remplace cette équipe. Mode édition live = §10.

### 10. Live sandbox on `/planning`

Mode édition seulement si `published[team]` existe. POST `/v1/live/sandbox/{team}/enter` (Bearer). Cuisine sans cycle : pas de bouton (409 API). Overlays = joujou (injecter le client live, ne pas appeler `/v1/sandbox/*`). Lecture quitte l’UI sans discard. Reload / ré-enter = GET/enter live (cran conservé). Publier → Cycles, sortir d’édition, l’autre équipe intacte. Tout annuler = discard live.

Hors slice : rotate invite-token, `optimized` 30 s.

## Risks / Trade-offs

- [Warning messages stay English] → French severity + optional French title from `code`; always keep `message`. Do not “fix” copy in the engine in this change.
- [Vite without API looks empty] → Document both processes; error state if `/v1` is down.
- [Temptation to match demo KPIs] → Spec forbids ratios absent from JSON.

## Migration Plan

Greenfield `web/`. Rollback = delete `web/` (and revert CORS if it was added). Example JSON and engine stay as they are.

## Open Questions

None that block this slice. `optimized` waits.
