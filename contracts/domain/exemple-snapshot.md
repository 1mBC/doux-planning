# Snapshot public Saint-Cloud (rewrite)

Freeze **domaine**. HTTP dual-read / pins UI = briefs Infra / UI ensuite.  
`GET /v1/examples/saint-cloud` reste **fichier** (pas un generate HTTP).

But : `/exemple` parle comme le live (messages FR + `wish_cols` nouveau modèle).  
**Pas** de `generate_cycle`. On garde la grille (92 shifts).

## Quoi réécrire

Fichier `data/examples/saint-cloud.json` :

| Bloc | Action |
|---|---|
| `restaurant` | **inchangé** (seed contexte) |
| `legal_context` / `id` | inchangé |
| `planning.assignments` | **inchangé** (92, mêmes shifts) |
| `planning.search_effort` / `calendars` / `seconds` | inchangé (`optimized`) |
| `planning.warnings` | `evaluate(draft)` sur restaurant + assignments du fichier |
| `planning.stats` / `legal_rows` / `wish_cols` / `wish_rows` | `cycle_recap` salle (même draft + result) |

Ne pas ajouter `legal_cols` (l’exemple UI lit `legal.rules`).  
`wish_cols` = clés live (`contrat`, `indispo`, `consecutive_rest`, …) — **plus** `we1j` / `weA` / `weB` / `soirs` / `repos2` / `coupures`.

## Invariants qui restent

- `stats.assignments` = `92` = `len(assignments)`
- `stats.empty` = `0` ; `stats.interdit` = `0` ; `stats.below_role` = `47`
- `stats.hours` = `416` / `494` / `84`
- Théo midi lundi A : `theo` / `day_index` 0 / `midday` / `660`–`960` / `5.0`
- Diane `contrat` : `{ ok: false, text: "30h · 29h / 39h" }`
- `warnings[].message` FR (freeze `cycle-recaps.md` warn-fr + déjà FR)

`stats.wellbeing` = `10` / `12`. `warnings.length` = `17`. (Core @ `609dd30`.)

## Tests

- Fichier : 92 assignments ; Théo 11h–16h ; Diane contrat inchangé ; aucun `we1j` / `weA`.
- Au moins un `contract_hours` et un `consecutive_rest_days` avec sous-chaîne FR (`contrat` / `pas deux repos`).
- Hydrate + seed exemple verts (restaurant inchangé → seed identique).
- Pytest domaine / engine / recap / board / hydrate verts. Pas `api/` / `web/`.

## Hors freeze

Seed HTTP, dual-read Postgres (`example_snapshots`), pins UI 10/12 / 17, exports, admin, archive / sync.
