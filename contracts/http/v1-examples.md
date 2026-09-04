# Tranche 0 — `GET /v1/examples/{example_id}`

Freeze HTTP pour le snapshot public Saint-Cloud.  
Source de vérité live aujourd’hui : `uvicorn doux_planning.api.app:app` (fichiers `data/`).  
Le JSON renvoyé n’est **pas** le fichier brut : `example_payload()` assemble `legal` + `restaurant` + `planning`.

## Route

```
GET /v1/examples/saint-cloud   → 200
GET /v1/examples/inconnu       → 404
```

- Pas d’auth.
- Pas de query, pas de body.
- Ne lance jamais `generate_cycle`, ni un job.
- `restaurant_id` n’apparaît pas dans le path.

Le body 404 n’est pas figé (FastAPI `detail` actuel OK). Le **200** l’est.

## Body 200 — clés racine (obligatoires)

```
{
  "example": "saint-cloud",
  "legal":     { ... },
  "restaurant": { ... },
  "planning":   { ... }
}
```

`restaurant` ne contient **pas** `legal_rules`.

### `legal`

| Clé | Invariant Saint-Cloud |
|---|---|
| `id` | `"france"` |
| `kind` | `"legal_context"` |
| `label` | présent |
| `rules[]` | les 6 ids : `rest_between_days`, `weekly_rest_days`, `max_coupure`, `max_daily_cuisine`, `max_daily_salle`, `max_weekly_hours` |
| `rules[].id` / `label_fr` / `severity` | présents |

### `restaurant` (clés utilisées par l’UI)

| Clé | Invariant |
|---|---|
| `id` | `"saint-cloud"` |
| `name` | `"Saint-Cloud"` |
| `team` | `"salle"` |
| `hours` | objet (mode / services / fermetures) |
| `employees[]` | profils ; chaque employé a `id`, `name`, `role` `{ name, level, team }`, `team` |

Les autres clés restaurant (`structures`, `source`, contrat, wellbeing…) peuvent rester. Ne pas les retirer. L’UI ne doit pas exiger plus que le tableau ci-dessus pour rendre la grille.

### `planning`

Clés obligatoires, dans cet ordre sémantique (l’ordre JSON n’est pas un contrat) :

`search_effort`, `calendars`, `seconds`, `assignments`, `warnings`, `stats`, `legal_rows`, `wish_cols`, `wish_rows`

| Clé | Invariant Saint-Cloud actuel |
|---|---|
| `search_effort` | `"optimized"` |
| `stats.assignments` | `92` |
| `stats.empty` | `0` |
| `stats.interdit` | `0` |
| `stats.below_role` | `43` |
| `stats.hours.assigned` | `416` |
| `stats.hours.contracted` | `494` |
| `stats.hours.percent` | `84` |
| `stats.wellbeing.held` | `21` |
| `stats.wellbeing.total` | `21` |
| `assignments.length` | `92` |
| `warnings.length` | `14` |

`stats.souhait` n’existe plus. Les manques d’heures de contrat sont dans `stats.hours` (`percent` = heures posées / heures contrat sur 14 j., arrondi). Les souhaits de bien-être (hors colonne `contrat` de `wish_rows`) sont dans `stats.wellbeing`. Pas de compteur « semaines à l’heure ».

### `planning.assignments[]`

`employee_id`, `day_index`, `weekday`, `service_id`, `team`, `start_minutes`, `end_minutes`, `post_level`, `duration_hours`

Ancre UI : Théo midi lundi semaine A = `employee_id: "theo"`, `day_index: 0`, `service_id: "midday"`, `start_minutes: 660`, `end_minutes: 960`, `duration_hours: 5.0`.

`service_id` : `"midday"` | `"evening"`.  
`day_index` : `0..13` (0–6 semaine A, 7–13 semaine B).

### `planning.warnings[]`

`severity`, `code`, `message`, `employee_id` (nullable), `day_index`

`message` est du texte moteur (souvent anglais). L’UI l’affiche, elle ne le réécrit pas en diagnostic.

### `planning.legal_rows[]` / `wish_cols` / `wish_rows[]`

- `legal_rows[]` : `name`, `employee_id`, `cells` map `{ rule_id: { ok, text } | absent }`
- `wish_cols[]` : `{ key, label }`
- `wish_rows[]` : `name`, `employee_id`, `cells` map `{ col_key: { ok, text } \| null }`

Ancre UI : cellule souhait Diane `contrat` = `{ "ok": false, "text": "30h · 29h / 39h" }`.  
Règle légale `max_daily_cuisine` : présente dans `legal.rules`, **aucune** cellule dans `legal_rows` Saint-Cloud → l’UI n’invente pas la colonne.

## Règles pour les agents

**UI**

- Un seul appel : `GET /v1/examples/saint-cloud`.
- Types TS = ce JSON. Pas d’autre route, pas de snapshot embarqué comme source de vérité, pas de score.
- Proxy Vite `/v1` → `http://127.0.0.1:8000`. Pas de CORS sauf si le proxy est inutilisable (alors demander).

**Infra**

- Peut changer le backing store (Postgres + seed) à condition que ce 200 reste identique sur les clés et invariants ci-dessus.
- Tant que l’UI tranche 0 n’est pas signée : si `DATABASE_URL` est **absent**, `uvicorn doux_planning.api.app:app --reload` doit **toujours** servir ce snapshot (comportement fichier actuel). Ne pas rendre Postgres obligatoire pour cette route avant OK orchestrateur.
- Ne pas toucher au moteur hors `api/`.
- Stop avant auth, jobs, sandbox, evaluate/swap/rank (tranches 1–2).

**Personne**

- Ne pas élargir ce contrat (nouveaux champs *requis* par l’UI, nouvelles routes).
- `legal_rows` / `wish_rows` existent **uniquement** sur ce snapshot figé, pas sur les futurs adapters live.
