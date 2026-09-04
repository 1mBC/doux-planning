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
