# Snapshot public Saint-Cloud (rewrite)

Freeze **domaine**. HTTP dual-read / pins UI = briefs Infra / UI ensuite.  
`GET /v1/examples/saint-cloud` reste **fichier** (pas un generate HTTP).

But : `/exemple` parle comme le live (**facts** + cellules `kind`/`payload`).  
**Pas** de `generate_cycle`. On garde la grille (92 shifts).

## Quoi réécrire

Fichier `data/examples/saint-cloud.json` :

| Bloc | Action |
|---|---|
| `restaurant` | **inchangé** (seed contexte) |
| `legal_context` / `id` | inchangé |
| `planning.assignments` | **inchangé** (92, mêmes shifts) |
| `planning.search_effort` / `calendars` / `seconds` | inchangé (`optimized`) |
| `planning.facts` | evaluate misses (payload) **puis** hits (`cycle_recap`) — **plus** `planning.warnings` |
| `planning.stats` / `legal_rows` / `wish_cols` / `wish_rows` / `score` | `cycle_recap` salle (même draft + result) |

Ne pas ajouter `legal_cols` (l’exemple UI lit `legal.rules`).  
`wish_cols` = clés live. Score **sans** `resumes`. Cellules **sans** `text`.

## Invariants qui restent

- `stats.assignments` = `92` = `len(assignments)`
- `stats.empty` = `0` ; `stats.interdit` = `0` ; `stats.below_role` = `47`
- `stats.hours` = `416` / `494` / `84`
- Théo midi lundi A : `theo` / `day_index` 0 / `midday` / `660`–`960` / `5.0`
- Diane `contrat` : `{ ok: false, kind: "contract_hours", payload: { hours_week_0: 30, hours_week_7: 29, contracted: 39 } }`
- Misses evaluate (`polarity == miss` et `kind != role_gap`) : **17**
- `stats.wellbeing` = `10` / `12`

Aucun `warnings`, `message`, `resumes`, `cell.text` dans le fichier réécrit.

## Tests

- Fichier : 92 assignments ; Théo 11h–16h ; Diane payload 30/29/39 ; aucun `we1j` / `weA`.
- 17 misses evaluate ; au moins un `contract_hours` miss et un `consecutive_rest_days` miss (payload, pas FR).
- Hydrate + seed exemple verts (restaurant inchangé → seed identique).
- Pytest domaine / engine / recap / board / hydrate verts. Pas `api/` / `web/` dans Core.

## UI `/exemple`

Lire le snapshot facts. Pastilles stats **92 / 0 / 0 / 47 / 84 % / 10 / 12**. Liste alertes = 17 misses evaluate, dictionnaire UI. Clic notes = miss puis hit. Diane 30h · 29h / 39h **composée UI**. Théo 11h–16h.

## Hors freeze

Keep-best. Archive / sync.
