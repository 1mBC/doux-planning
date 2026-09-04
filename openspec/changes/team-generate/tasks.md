## 1. Published cycles and generate_team

- [x] 1.1 Add `published_cycles` (salle/cuisine, default both None) and verify an empty restaurant has neither cycle
- [x] 1.2 Implement `generate_team` (ready → expand + one-team draft + `generate_cycle`; not ready → `TeamNotReady` without solve) and verify salle minimal assignments are salle-only, cuisine raises, and a second salle generate replaces salle

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `api/`, `contracts/`, engine formulas / `SEARCH_SECONDS`, preview/fill, or Saint-Cloud hydrate
