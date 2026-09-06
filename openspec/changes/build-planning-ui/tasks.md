## 1. Scaffold

- [x] 1.1 Create `web/` as a Vite + React + TypeScript app (French `index.html` title) and verify `npm install` then `npm run build` succeed
- [x] 1.2 Proxy Vite `/v1` to `http://127.0.0.1:8000` and verify a browser request from the SPA origin to `/v1/examples/saint-cloud` reaches uvicorn (no new FastAPI route; no CORS unless the proxy cannot be used)

## 2. Snapshot client

- [x] 2.1 Add TypeScript types for the example payload (`legal`, `restaurant`, `planning`) and a loader that calls only `GET /v1/examples/saint-cloud`; verify a missing/failed response shows a French error and does not render a fake grid
- [x] 2.2 On 200, render restaurant name and `planning.search_effort` / `calendars` / `seconds` as chrome only; verify values match the JSON (e.g. Saint-Cloud, optimized)

## 3. First useful screen

- [x] 3.1 Show `planning.stats` counters (`assignments`, `empty`, `interdit`, `below_role`, `hours.percent` as « Heures vs contrat », `wellbeing.held` / `wellbeing.total` as « Souhaits bien-être ») and verify they equal the payload (92 / 0 / 0 / 47 / 84 % / 10 / 12) without displaying assigned/contracted, `stats.souhait`, or a semaines-à-l’heure ratio
- [x] 3.2 Render week A and week B paper grids (role groups, person + midi/soir, début/fin/H, empty = repos, post level in parentheses when below role) from `assignments` + `employees`; verify Théo midi lundi semaine A is 11h–16h 5h and that no assignment is invented
- [x] 3.3 List every `planning.warnings` item (French severity label, engine `message` kept) and verify the list length equals `warnings.length` (17 on the current snapshot)
- [x] 3.4 Render the legal table from `legal.rules` + `legal_rows` (omit rules with no cells) and the wish table from `wish_cols` + `wish_rows`; verify cuisine 11 h/j is absent and Diane contrat text is the payload’s `30h · 29h / 39h`

## 4. Product polish

- [x] 4.1 Apply paper-grid styling (sticky names, person tint, horizontal scroll) in the form of the GitHub Pages demo, not its hardcoded numbers; verify desktop layout in the browser (IronBee)
- [x] 4.2 Document `uvicorn` + `npm run dev` in the root README and verify a new reader can open the French read-only screen without editing `src/doux_planning/` outside `api/`

## 5. Auth screens

- [x] 5.1 Types + loaders for login / register / logout / `GET /v1/me` / `GET /v1/invites/{company_code}` matching `contracts/http/v1-auth.md`; missing keys throw; Bearer never on examples or sandbox
- [x] 5.2 Login (email + password) and register (`/register`, Entreprise / Salarié, no company name, employee fiches then `employee_id`, QR query locks salarié + `employee_token`); password ≥ 8; show API `detail`; no mot de passe oublié
- [x] 5.3 `sessionStorage` token; session chrome (email + kind + Déconnexion); reload `GET /v1/me` (401 → login); example reachable without session (« Voir l’exemple »)
- [x] 5.4 `kind: employee` hides Mode édition and shows the later-planning sentence; `kind: company` keeps grid + sandbox; bump `web/` to 0.7.0
- [x] 5.5 Verify `npm run build`; company login → `/me` → logout; employee register (fiches + QR); example 92 assignments without session; employee has no Mode édition; version bar `v0.7.0`

## 6. Context wizard

- [x] 6.1 Types + GET/PATCH `/v1/context` matching the contract; missing keys throw; Bearer only on context (+ existing auth); never on example/sandbox
- [x] 6.2 Company `/context` (after login/register + « Mon restaurant »): identity banner, sequential wizard roles → fiches → services → types → semaine, both teams, full-list PATCH rules, invite URL, no rotate, no generate
- [x] 6.3 Show `ready.*` as JSON badges; employee cannot open `/context`; bump `web/` to 0.8.0
- [x] 6.4 Verify `npm run build`; company salle 5 steps → `ready.salle` true / `ready.cuisine` false; reload same context; employee stays off wizard; example 92 without session; `v0.8.0`

## 7. Team generate

- [x] 7.1 Types + GET `/v1/cycles` + POST `/v1/generate` matching the contract; missing keys throw; Bearer on generate/cycles (+ existing auth/context); never on example/sandbox
- [x] 7.2 Company `/planning` (chrome « Planning »): load cycles + context, team selector, Calculer iff `ready[team]`, POST `minimal`, grid + warnings, no invented stats/legal/wish, no sandbox on this cycle
- [x] 7.3 Cuisine null / not ready: empty + « Pas encore calculé », salle intacte; employee cannot open `/planning`; bump `web/` to 0.9.0
- [x] 7.4 Verify `npm run build`; salle ready → Calculer → cells + warnings; cuisine button off; reload keeps salle; employee stays off planning; example 92 without session; `v0.9.0`

## 8. Live sandbox

- [x] 8.1 Distinct live client `/v1/live/sandbox/{team}/…` + Bearer; parse LiveState (`team` required); reuse parsers; never call `/v1/sandbox/*` from `/planning`
- [x] 8.2 `/planning` Mode édition if published[team]; overlays + history + Annuler + Tout annuler; Lecture without discard; Publier updates cycles
- [x] 8.3 Cuisine without cycle: no edit; `/exemple` joujou unchanged; bump `web/` to 0.10.0
- [x] 8.4 Verify `npm run build`; salle edit retune → Lecture keeps cran → Publier → reload; example enter without session still 92; `v0.10.0`

## 9. Employee board

- [x] 9.1 Types + GET `/v1/me/planning` matching the contract; missing keys throw; Bearer on me/planning (+ existing auth); never on example/sandbox
- [x] 9.2 Employee `/planning` (after login/register + chrome « Planning »): team grid, me highlight, muted colleagues, empty → « Pas encore publié », read-only contract / unavail / wishes panel; no Calculer / Mode édition / wizard
- [x] 9.3 Company `/planning` / `/context` / live unchanged; `/exemple` joujou unchanged; remove later-planning sentence; bump `web/` to 0.11.0
- [x] 9.4 Verify `npm run build`; employee with published salle fiche → team grid + color + panel; company `/planning` keeps Calculer; example 92 without session; `v0.11.0`

## 10. Wellbeing wizard

- [x] 10.1 Context types: wellbeing object, indispos `{ weekday, service_id }`, `week_labels`; drop `WELLBEING_KEYS` / `every_*`; employee wishes `{ kind, held, … }`
- [x] 10.2 Tabs Rôles → Équipe → Souhaits bien-être → Services → Types → Semaine type; Équipe popup jour×service; Souhaits columns; wishes not a ready gate
- [x] 10.3 Labels A/B vs Paire/Impaire on semaine type + company/employee grids; exemple stats from JSON (92 / 17 / 10/12 / 47); bump `web/` to 0.12.0
- [x] 10.4 Verify `npm run build`; popup 2 jours × 1 service → 2 créneaux; radio we paire → `week_labels` parity; reload persists; employee reads new wishes; exemple 92; `v0.12.0`

## 11. Seed example

- [x] 11.1 `POST /v1/context/seed-example` Bearer, no body; 200 parsed as GET Context; `detail` on error
- [x] 11.2 Company `/context` banner button **Intégrer l’exemple Saint-Cloud** (empty or filled) + one-sentence FR confirm; stay on `/context`; unlock salle tabs; no generate
- [x] 11.3 No button on employee / exemple / planning / login; bump `web/` to 0.13.0
- [x] 11.4 Verify `npm run build`; empty company → confirm → POST → Diane/Théo + semaine + salle ready; reload persists; second click overwrites; exemple 92; `v0.13.0`

## 12. Weekend rest + Services-first types

- [x] 12.1 Tabs Services → Rôles → Équipe → Souhaits → Services types → Semaine type; uncheck service → FR warning + purge both teams; non-offered invisible
- [x] 12.2 `weekend_rest_day` required bool + checkbox beside we radio; max_services = offered only; employee `kind: weekend_rest_day` same label
- [x] 12.3 Services types: offered-service subtabs, Ajouter un type, ladder pickers, bag + worst-case `remaining_post_levels`; bump `web/` to 0.14.0
- [x] 12.4 Verify `npm run build`; Services first; uncheck PDJ after types → gone; repos we persists; 2 arrivées + 1 départ (freeze bags); employee reads wish; exemple 92; `v0.14.0`

## 13. One-line types + live recaps

- [x] 13.1 Services types: chronological one-line events, +/− per level, STAFF après, worst-case persist
- [x] 13.2 Parse cycle `stats` / `legal_*` / `wish_*` (throw if missing); pastilles + 2 tables hors édition; hide in Mode édition; warning `message` as-is
- [x] 13.3 `/exemple` snapshot unchanged; bump `web/` to 0.15.0
- [x] 13.4 Verify `npm run build`; 2 arrivées + 1 départ on lines + STAFF + reload; Calculer recaps; edit hides them; 11 h clocks if present; exemple 92; `v0.15.0`

## 14. Chrome polish (contrat, orange, invite)

- [x] 14.1 Warning `contract_hours` → pastille Contrat ; cellules `ok: false` orange + gras ; titre **Souhaits bien-être** ; Calculer / Mode édition sous Salle · Cuisine
- [x] 14.2 Types : horloge + ±15 collés, STAFF en en-tête seulement, N lisible ; rôles stepper ; plus de sous-texte we ; invite popup URL + QR
- [x] 14.3 `/exemple` même chrome, snapshot inchangé ; bump `web/` to 0.16.0
- [x] 14.4 Verify `npm run build` ; contrat / orange / titre / Calculer sous équipes ; types persistés ; rôles ; invite QR ; plus de jeton / sous-texte we ; exemple 92 ; `v0.16.0`

## 15. Refreshed exemple snapshot (FR + wish live)

- [x] 15.1 `/exemple` reads refreshed JSON as-is: pastilles 92 / 0 / 0 / 47 / 84 % / 10 / 12 ; 17 warnings FR ; `wish_cols` live (no `we1j` / `weA`) ; Diane `30h · 29h / 39h` orange ; Théo 11h–16h ; bump `web/` to 0.17.0
- [x] 15.2 Verify `npm run build` ; `/exemple` sans session : 92, 17 alertes FR (« contrat », « pas deux repos »), 10/12, colonnes live, Diane orange, Théo 11h–16h ; `/planning` company inchangé hors parse ; `v0.17.0`
