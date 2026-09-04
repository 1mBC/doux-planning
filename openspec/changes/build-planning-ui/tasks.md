## 1. Scaffold

- [x] 1.1 Create `web/` as a Vite + React + TypeScript app (French `index.html` title) and verify `npm install` then `npm run build` succeed
- [x] 1.2 Proxy Vite `/v1` to `http://127.0.0.1:8000` and verify a browser request from the SPA origin to `/v1/examples/saint-cloud` reaches uvicorn (no new FastAPI route; no CORS unless the proxy cannot be used)

## 2. Snapshot client

- [x] 2.1 Add TypeScript types for the example payload (`legal`, `restaurant`, `planning`) and a loader that calls only `GET /v1/examples/saint-cloud`; verify a missing/failed response shows a French error and does not render a fake grid
- [x] 2.2 On 200, render restaurant name and `planning.search_effort` / `calendars` / `seconds` as chrome only; verify values match the JSON (e.g. Saint-Cloud, optimized)

## 3. First useful screen

- [x] 3.1 Show `planning.stats` counters (`assignments`, `empty`, `interdit`, `below_role`, `hours.percent` as « Heures vs contrat », `wellbeing.held` / `wellbeing.total` as « Souhaits bien-être ») and verify they equal the payload (92 / 0 / 0 / 43 / 84 % / 21 / 21) without displaying assigned/contracted, `stats.souhait`, or a semaines-à-l’heure ratio
- [x] 3.2 Render week A and week B paper grids (role groups, person + midi/soir, début/fin/H, empty = repos, post level in parentheses when below role) from `assignments` + `employees`; verify Théo midi lundi semaine A is 11h–16h 5h and that no assignment is invented
- [x] 3.3 List every `planning.warnings` item (French severity label, engine `message` kept) and verify the list length equals `warnings.length` (14 on the current snapshot)
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
