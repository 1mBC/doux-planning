# Banc de jeux (admin)

Freeze **domaine** + HTTP admin. UI = brief UI.  
**Salle only.** Catalogue `data/bench/`.  
Le banc **ne lit / n’écrit jamais** `published_cycles`, `live_sandboxes`, comptes, generate_logs. State **jetable**. Jobs bench ≠ jobs resto (pas de 409 croisé).

## Identité moteur

Un nom par version de moteur : `engine_ref`. **Une** source : `trim(data/bench/VERSION)` (une ligne).  
Ce n’est **pas** le numéro UI (`web/src/release.ts`).

Cette tranche : `core-0` (moteur actuel, **aucun** change fill / SAT / keep-best).  
HTTP et rows émettent `engine_ref` **et** `app_version` = **le même string** (alias, une seule source).

Vieux runs `app_version = "0.27.0"` : à la **lecture** `engine_ref = "core-0"` (même moteur). On n’écrit plus `0.27.0`.

Retour arrière = revert git du land Core, puis relancer. **Pas** de bouton, **pas** de second fill dans le process.

## Catalogue (repo)

```
data/bench/VERSION          # une ligne = engine_ref, ex. core-0
data/bench/{category}/{id}/context.json
data/bench/{category}/{id}/expected.json
```

Catégories **figées** (ordre d’affichage) :

| `category` | `id` | Particularité |
|---|---|---|
| `tight` | `halles` | sous-effectif / couverture |
| `clock` | `nocturne` | horloges 11 h (soir tard → midi tôt) |
| `wishes` | `campus` | indispos + we + max services |
| `ladder` | `brigade` | 1 senior, postes 2 |
| `crafted` | `atelier` | témoin construit, globale 10 |
| `crafted` | `rivoli` | témoin we pair / impair, globale 10 |
| `crafted` | `marais` | témoin 0 dîner + repos collés, globale 10 |

`crafted` = planning **d’abord**, contexte **déduit** (heures pile, souhaits déjà tenus). Oracle = **Manuel** (plus tard : plannings de restos réels).  
Scan disque. Jeu sans les deux JSON → **omit**, pas 500.  
`engine_ref()` = trim `data/bench/VERSION`.

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

Planning **manuel**. `evaluate` → **0 interdit**. `crafted` : `cycle_score` globale **≥ 9,5**. Notes recalculées au run.

## Core

```
engine_ref() -> str            # trim VERSION
list_bench_datasets() -> [ … ]   # ordre : tight, clock, wishes, ladder, crafted (puis id)
load_bench_dataset(category, id) -> BenchDataset
run_bench(category, id, effort) -> BenchOutcome
UnknownBenchDataset
```

`run_bench` : copie jetable + `generate_cycle` + **le même recap que le live** ×2 (Modèle + Manuel) + `deltas` (Modèle − Manuel).  
`BenchOutcome.engine_ref` = `engine_ref()` au moment du run.  
**Zéro** `published_cycles`. Keep-best / `SEARCH_*` inchangés. Tests generate = **`minimal`**.

### Recap unique

```
cycle_recap_from_draft(draft, result) -> CycleRecap
```

Même objet que `cycle_recap` live (`stats`, legal/wish, `facts` miss puis hit, `score` sans resumes).  
`cycle_recap(state, team)` **appelle** ce helper (pas une 2ᵉ formule).  
Banc : `run_bench` l’appelle sur le draft généré **et** sur `expected` (`evaluate` + recap, pas de 2ᵉ solve).  
`BenchOutcome` : `facts` + `expected_facts` = `recap.facts` (liste **complète**, pas seulement evaluate misses). `engine_ref` présent.

## HTTP (admin)

Routes run / jobs / datasets **inchangées** (plus `engine_ref` / `app_version` alias sur summaries). `POST all` / `category=crafted` = un job par jeu.  
Persist : colonne existante `bench_runs.app_version` = `outcome.engine_ref`. **Pas** d’Alembic.

**Last-run** = le plus récent par `(category, dataset_id, search_effort, engine_ref)`.  
Export / compare-chemin = last-run du **`engine_ref` courant** (VERSION).  
Tableau Banc = **toutes** les refs (`GET /versions`), les trois computes.  
Un nouveau run **n’écrase pas** les scores d’un autre `engine_ref`.

Vieux `"0.27.0"` lu comme `"core-0"`.

### GET compare (moteur courant)

`GET /v1/admin/bench/compare/{category}/{dataset_id}/{search_effort}`

200 : last-run du `engine_ref` **courant** + `CycleSlice` des deux côtés — **recalculé** via `cycle_recap_from_draft` (assignments persistés + `expected.json` + contexte). Vieux `bench_runs.warnings` ignore : on ne s’en sert plus comme source.  
Pas de run pour ce trio + ref courant → 404.

```
{
  …summary,                 # + engine_ref et app_version (= même string)
  employees: [{ id, name, role, team }],
  model: CycleSlice,
  manual: CycleSlice
}
```

`CycleSlice` = `{ assignments, facts, score, stats, legal_cols, legal_rows, wish_cols, wish_rows }`  
Libellés UI : Modèle / Manuel. Clés JSON `model` / `manual`. Plus d’alias plats `facts` = warnings.

### GET compare d’un run

`GET /v1/admin/bench/runs/{run_id}`

Route **déjà là**. 200 = **même forme que compare** (`employees`, `model`, `manual` + summary `engine_ref` / `app_version`). Plus d’alias plats `assignments` / `facts` au top-level. 404 si id inconnu.

### GET versions (matrice)

`GET /v1/admin/bench/versions`

```
{
  engine_ref,                    # VERSION courant
  engine_refs: ["core-0", …],    # refs qui ont ≥1 run ; 0.27.0 fusionné en core-0 ; ordre = 1re apparition
  datasets: [
    {
      category, id, name, challenge_fr,
      manual: { global },        # expected_score du 1er run connu ; null si jamais run
      by_ref: {
        "core-0": {
          minimal: { run_id, global, deltas, duration_seconds } | null,
          optimized: … | null,
          maximal: … | null
        }
      }
    }
  ]
}
```

Ordre `datasets` = `list_bench_datasets`. Clés d’effort toujours les trois, `null` si pas de run.  
403 / 401 / 503 comme le reste.

### GET export pack

```
GET /v1/admin/bench/export?scope=dataset&category=&dataset_id=
GET /v1/admin/bench/export?scope=below_manuel
```

Bearer admin. 403 / 401 / 503 comme le reste.  
`scope=dataset` sans run → 404. `below_manuel` vide → 200 `{ … datasets: [] }`.

**below_manuel** / export dataset = last-run du **`engine_ref` courant** seulement.  
`score.global < expected_score.global` (les deux non null). Un jeu entre dans le pack s’il a **au moins un** effort courant sous le Manuel. Pour ces jeux : **tous** les efforts courants qui ont un run. Chaque effort a `below_manuel: bool` + `engine_ref` + `run_id`.

200 :

```
{
  export_version: 1,
  kind: "bench-pack",
  engine_ref,                  # courant
  app_version,                 # = engine_ref
  exported_at,                 # ISO UTC
  scope: "dataset" | "below_manuel",
  datasets: [
    {
      category, id, name, challenge_fr,
      context,                   # JSON catalogue (hours, roles, types, employees complets — pas invite_token)
      manual: CycleSlice,        # expected.json + recap ; identique pour tous les efforts
      efforts: [
        {
          search_effort,
          run_id,
          engine_ref,
          duration_seconds,
          below_manuel,
          model: CycleSlice,
          deltas
        }
      ]
    }
  ]
}
```

Ordre datasets = `list_bench_datasets`. Efforts = minimal → optimized → maximal s’ils existent.  
Pas d’Alembic (recompute). Keep-best inchangé.

## UI

Company **`me.admin`**.  
Menu **à plat** : **Historique des computes | Banc**. **Plus** d’entrée Versions. `/admin/bench/versions` → **redirige** vers `/admin/bench`. SPA `/admin/bench/run/{run_id}` inchangé.

**Un seul tableau** (Banc). Source : `GET /v1/admin/bench/versions` (plus le last-run courant seul).

Pour **chaque** compute (Minimal, Optimisé, Maximal) :

```
<effort>
  Manuel | {engine_ref} | {engine_ref} | …
```

- **Manuel** : `dataset.manual.global` (même chiffre pour les trois efforts).  
- **Chaque `engine_ref`** : globale Modèle + delta vs Manuel. Tiret si pas de run.  
- Clic cellule moteur → `/admin/bench/run/{run_id}` (compare de **ce** run).  
- Clic Manuel → compare-chemin de cet effort (last-run courant), comme aujourd’hui.

Lancer / export **inchangés**. Sous-titre : `moteur {engine_ref}` = VERSION courant (celui qu’on lance). Pas de bouton revert.

Compare chemin existant = last-run courant, inchangé.

**Pastilles score** (`CycleScoreNotes`) — **partout** (planning, exemple, banc) :

1. titre (Couverture /10, Globale /10, …)  
2. **même ligne** : note + jauge  
3. ligne suivante : totaux (`score-facts.md` résumés). Globale : pas de totaux.  
4. clic → détail miss puis hit  

Compare : **même** `CycleScoreNotes` des deux côtés, avec `facts` + `stats` + rows + `employees` (noms réels, plus l’id). Grilles inchangées. Pas d’édition.

**Exporter pack** (JSON, download navigateur, pas de 2ᵉ formule) :

- Page compare **et** ligne tableau : **Exporter ce jeu** → `scope=dataset`  
- Tableau banc : **Exporter sous le Manuel** → `scope=below_manuel`  

Fichiers : `bench-{category}-{id}.json` / `bench-below-manuel.json`.

**`0.34.0`**, note FR : banc, tous les computes, une colonne par version moteur.

## Tests

HTTP / Core **inchangés** (déjà landés).  
UI : menu 2 entrées (plus Versions). Tableau Banc : 3 computes × (Manuel + une col par `engine_refs`). Deux refs → deux colonnes moteur **sous Minimal et sous Optimisé et sous Maximal**. Clic `core-0` Maximal ouvre `/admin/bench/run/{id}`. `/admin/bench/versions` ramène au Banc. Barre v0.34.0.

## Hors freeze

Plafonds de services durs (`core-1`) — **après** cette file. Bouton revert. Deux fills dans le même process. Jeux cuisine. CSV/XLSX banc. Archive / sync.
