# Banc de jeux (admin)

Freeze **domaine** + HTTP admin. UI = brief UI.  
**Salle only.** 4 catégories × 1 jeu dans `data/bench/`.  
Le banc **ne lit / n’écrit jamais** `published_cycles`, `live_sandboxes`, comptes, generate_logs. State **jetable**. Jobs bench ≠ jobs resto (pas de 409 croisé).

Versions de moteur plus tard : on persiste `app_version` maintenant, pas de dashboard d’historique dans cette tranche.

## Catalogue (repo)

```
data/bench/VERSION          # une ligne, ex. 0.27.0
data/bench/{category}/{id}/context.json
data/bench/{category}/{id}/expected.json
```

Catégories **figées** :

| `category` | `id` | Particularité |
|---|---|---|
| `tight` | `halles` | sous-effectif / couverture |
| `clock` | `nocturne` | horloges 11 h (soir tard → midi tôt) |
| `wishes` | `campus` | indispos + we + max services |
| `ladder` | `brigade` | 1 senior, postes 2 |

Scan disque au boot / à chaque list. Jeu sans les deux JSON → **omit**, pas 500.  
`app_version` = contenu trim de `data/bench/VERSION` (orchestrateur). Persisté **tel quel** sur chaque run.

### `context.json`

Contexte **live** (pas le snapshot Saint-Cloud) :

```
{
  id, category, name, team: "salle", challenge_fr,
  hours: { mode: "services", services: ["midday","evening"], closed_weekdays: ["sunday"] },
  roles: [{ name, level, team: "salle" }],
  types: [{ id, name, team, service_id, arrivals, departures }],
  employees: [{ id, name, role: {name, level, team}, team, contractual_hours_per_week,
                unavailabilities?, wellbeing?, min_shift_hours? }]
}
```

Pas de `invite_token` (généré au load, ≠ id).  
`typical_week` **dérivée** : pour chaque `roles.team` × `hours.services` × 7 weekdays — `closed` ssi weekday ∈ `closed_weekdays` ; sinon `type_id` = l’unique type `(team, service)`.  
`team_ready(salle)` **vrai** après load. Cuisine absente.

### `expected.json`

```
{ assignments: [{ employee_id, day_index, weekday, service_id, team, start_minutes, end_minutes, post_level }] }
```

Oracle **humain** (pas un Maximal figé). `evaluate` → **0 interdit**. Notes = `cycle_score` au moment du run (pas stockées dans le fichier).

## Core

```
BenchDataset          # meta + state jetable + expected assignments
list_bench_datasets() -> [ { category, id, name, challenge_fr } ]
load_bench_dataset(category, id) -> BenchDataset
run_bench(category, id, effort) -> BenchOutcome
UnknownBenchDataset
```

`run_bench` :

1. `load_bench_dataset` (state **copie**, jamais le resto d’un compte).
2. `expand_typical_week` → draft salle + `generate_cycle(draft, effort)`.
3. `cycle_score` sur le résultat **et** sur `expected` (même draft, assignments oracle).
4. `deltas[axe] = note_gen − note_expected` (`null` si une des deux notes est `null`). Idem `global`.

**Interdit** : `generate_team` sur un `RestaurantState` persisté ; écrire `published_cycles`.  
Keep-best / `SEARCH_*` **inchangés**. Tests generate = **`minimal`** seulement (pas 30 s / 600 s).

`BenchOutcome` : `{ category, id, search_effort, duration_seconds, assignments, warnings, score, expected_score, deltas }`.

## HTTP (admin)

Bearer. `admin !== true` → 403 `Action réservée à l’admin.` Employee 403. Sans session 401. Sans DB 503.

```
GET  /v1/admin/bench/datasets
GET  /v1/admin/bench/runs                  ?category & dataset_id  (optionnel)
POST /v1/admin/bench/run
GET  /v1/admin/bench/jobs/{job_id}
GET  /v1/admin/bench/runs/{run_id}
GET  /v1/admin/bench/compare/{category}/{dataset_id}/{search_effort}
```

`POST /v1/admin/bench/run` :

```
{ scope: "all"|"category"|"dataset", category?, dataset_id?, search_effort }
```

`scope=category` exige `category`. `scope=dataset` exige `category` + `dataset_id`. Effort / scope invalide → 400. Dataset inconnu → 404.

| Cas | HTTP |
|---|---|
| `dataset` + `minimal` \| `optimized` | **200** `{ runs: [RunSummary] }` sync dans la requête |
| `all` \| `category` \| `maximal` | **202** `{ job_ids, status: queued }` — **un job par jeu** |

Worker : même process que le Maximal resto, table **`bench_jobs`** (≠ `generate_jobs`). Pas de 409 avec un Maximal client. Chaque job `done` → **une** ligne `bench_runs` (même si l’UI est partie). Échec → `failed` + `error` FR, **pas** de run.

`RunSummary` : `{ id, created_at ISO, app_version, category, dataset_id, search_effort, duration_seconds, score, expected_score, deltas }` — **pas** d’assignments.  
`GET .../runs` : **tous** les runs, plus récent d’abord. Filtres optionnels.  
`GET .../runs/{id}` : summary **+** `assignments` + `warnings` du généré.  
`GET .../compare/...` : **dernier** run de ce `(category, id, effort)` + `expected.assignments` + `expected_score`. 404 si aucun run.

Pas d’Alembic sur les JSON du repo. Tables : `bench_jobs`, `bench_runs` (JSONB scores / assignments).

SPA : `/admin`, `/admin/bench`, `/admin/bench/{category}/{dataset_id}/{search_effort}`.

## UI

Company **`me.admin`**. Lien **Banc** sur `/admin` (le log generate **reste**).  
`/admin/bench` : boutons lancer — toutes les catégories | une catégorie | un jeu — × Minimal / Optimisé / Maximal.  
Tableau : **une ligne par jeu**, colonnes des 3 efforts = **dernier** run (globale générée · globale oracle · Δ globale). Tiret si pas de run. Clic → page compare.  
Maximal / all / category : 202 + poll jobs **ou** refresh `GET runs` ; quitter la page **OK** (résultat en DB).

`/admin/bench/{category}/{id}/{effort}` : titre `catégorie · id · effort`. **Planning généré** (dernier run) puis **planning oracle**. Mêmes notes + resumes. Grille comme `/planning` (lecture, pas d’édition). 404 / vide → message FR.

**`0.28.0`**, note FR : banc admin 4 jeux.

## Tests

Core : 4 jeux listés ; load → `team_ready(salle)` ; `evaluate(expected)` 0 interdit ; `run_bench(..., minimal)` a `score` + `expected_score` + `deltas` ; un `RestaurantState` live **inchangé** après `run_bench`.  
Infra : POST dataset minimal 200 + row DB ; POST all maximal 202 + tick stub → rows ; GET compare ; 403 non-admin ; generate_team client **intact**.  
UI : build ; `/admin/bench` table ; clic compare. Barre v0.28.0.

## Hors freeze

Dashboard historique des notes. Plusieurs `engine_ref`. Jeux cuisine. Rewrite Saint-Cloud. Archive / sync.
