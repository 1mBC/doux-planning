# Banc de jeux (admin)

Freeze **domaine** + HTTP admin. UI = brief UI.  
**Salle only.** Catalogue `data/bench/`.  
Le banc **ne lit / n’écrit jamais** `published_cycles`, `live_sandboxes`, comptes, generate_logs. State **jetable**. Jobs bench ≠ jobs resto (pas de 409 croisé).

Versions de moteur plus tard : on persiste `app_version` maintenant, pas de dashboard d’historique dans cette tranche.

## Catalogue (repo)

```
data/bench/VERSION          # une ligne, ex. 0.27.0
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
`app_version` = trim `data/bench/VERSION`.

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
list_bench_datasets() -> [ … ]   # ordre : tight, clock, wishes, ladder, crafted (puis id)
load_bench_dataset(category, id) -> BenchDataset
run_bench(category, id, effort) -> BenchOutcome
UnknownBenchDataset
```

`run_bench` : copie jetable + `generate_cycle` + **le même recap que le live** ×2 (Modèle + Manuel) + `deltas` (Modèle − Manuel).  
**Zéro** `published_cycles`. Keep-best / `SEARCH_*` inchangés. Tests generate = **`minimal`**.

### Recap unique

```
cycle_recap_from_draft(draft, result) -> CycleRecap
```

Même objet que `cycle_recap` live (`stats`, legal/wish, `facts` miss puis hit, `score` sans resumes).  
`cycle_recap(state, team)` **appelle** ce helper (pas une 2ᵉ formule).  
Banc : `run_bench` l’appelle sur le draft généré **et** sur `expected` (`evaluate` + recap, pas de 2ᵉ solve).  
`BenchOutcome` : `facts` + `expected_facts` = `recap.facts` (liste **complète**, pas seulement evaluate misses).

## HTTP (admin)

Routes run / jobs / datasets **inchangées**. `POST all` / `category=crafted` = un job par jeu.

### GET compare

`GET /v1/admin/bench/compare/{category}/{dataset_id}/{search_effort}`

200 : summary run **plus** un `CycleSlice` par côté — **recalculé** via `cycle_recap_from_draft` (assignments persistés + `expected.json` + contexte). Vieux `bench_runs.warnings` ignore : on ne s’en sert plus comme source.

```
{
  …summary,
  employees: [{ id, name, role, team }],
  model: CycleSlice,
  manual: CycleSlice
}
```

`CycleSlice` = `{ assignments, facts, score, stats, legal_cols, legal_rows, wish_cols, wish_rows }`  
Libellés UI : Modèle / Manuel. Clés JSON `model` / `manual`. Plus d’alias plats `facts` = warnings.

### GET export pack

```
GET /v1/admin/bench/export?scope=dataset&category=&dataset_id=
GET /v1/admin/bench/export?scope=below_manuel
```

Bearer admin. 403 / 401 / 503 comme le reste.  
`scope=dataset` sans run → 404. `below_manuel` vide → 200 `{ … datasets: [] }`.

**below_manuel** = `score.global < expected_score.global` (les deux non null). Un jeu entre dans le pack s’il a **au moins un** effort last-run sous le Manuel. Pour ces jeux : **tous** les efforts qui ont un run (pas seulement les perdants) — plus utile pour comparer. Chaque effort a `below_manuel: bool`.

200 :

```
{
  export_version: 1,
  kind: "bench-pack",
  app_version,
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

Company **`me.admin`**. Menu + tableau (Modèle | Manuel | Delta) **inchangés**.

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

**`0.31.0`**, note FR : banc même notes que le live, export pack, pastille titre puis note+jauge.

## Tests

Core : `cycle_recap_from_draft` = même facts que live. `run_bench(tight, halles, minimal)` : `facts` a des hits (`post_held` ou `role_gap` hit) ; `expected_facts` non vide ; 0 interdit sur expected ; `published_cycles` intact. Keep-best inchangé.  
Infra : GET compare a `model.facts` + `manual.facts` (pas seulement misses). GET export dataset halles si un run existe. GET `below_manuel` 200. 403 non-admin.  
UI : compare clic Occupation = miss **et** hit des deux blocs. Pastille = titre / note+jauge / totaux. Deux boutons export. Barre v0.31.0.

## Hors freeze

Dashboard historique. `engine_ref`. Jeux cuisine. CSV/XLSX banc. Archive / sync.
