# Banc de jeux (admin)

Freeze **domaine** + HTTP admin. UI = brief UI.  
**Salle only.** Catalogue `data/bench/`.  
Le banc **ne lit / n’écrit jamais** `published_cycles`, `live_sandboxes`, comptes, generate_logs. State **jetable**. Jobs bench ≠ jobs resto (pas de 409 croisé).

## Identité moteur

Un nom par version de moteur : `engine_ref`. **Une** source : `trim(data/bench/VERSION)` (une ligne).  
Ce n’est **pas** le numéro UI (`web/src/release.ts`).

`core-3` = seeds → SAT (locks) → fill (`contracts/domain/engine-seeds.md`). `core-2` = fill **fewest**. `core-1` = plafonds durs, ordre chrono. `core-0` = avant les plafonds.  
HTTP et rows émettent `engine_ref` **et** `app_version` = **le même string** (alias, une seule source).

Vieux runs `app_version = "0.27.0"` : à la **lecture** `engine_ref = "core-0"` (même moteur). On n’écrit plus `0.27.0`.

Retour arrière = revert git du land Core, puis relancer. **Pas** de bouton, **pas** de second fill dans le process.

## Catalogue (repo)

```
data/bench/VERSION          # une ligne = engine_ref, ex. core-0
data/bench/{category}/{id}/context.json
data/bench/{category}/{id}/expected.json
```

Catégories **figées** (ordre d’affichage) — **50 jeux**. Les **30** déjà au catalogue **bit-à-bit inchangés** (fichiers + oracles). **+ 20** `crafted` (oracles).

| `category` | `id` | Particularité |
|---|---|---|
| `tight` | `halles` | sous-effectif (ancien) |
| `tight` | `quai` | sous-effectif, **3 services** |
| `tight` | `marche` | sous-effectif, L1–L3 |
| `clock` | `nocturne` | 11 h (ancien) |
| `clock` | `aube` | soir tard → **petit-déj**, 3 services |
| `clock` | `brasserie` | 2 types midi (semaine / samedi) |
| `wishes` | `campus` | indispos + we (ancien) |
| `wishes` | `canal` | indispos + **L4+ à 0 dîner** |
| `wishes` | `butte` | max services + we |
| `ladder` | `brigade` | L3 vs L1 (ancien) |
| `ladder` | `pyramide` | **L1→L6** |
| `ladder` | `sommet` | un seul L6 |
| `ladder` | `jumeaux` | deux L6 |
| `ladder` | `trou` | L1–L6 **sans L3** |
| `crafted` | `atelier` | témoin (ancien) |
| `crafted` | `rivoli` | témoin we (ancien) |
| `crafted` | `marais` | témoin 0 dîner (ancien) |
| `crafted` | `temple` | oracle ≥ 9,5, **3 services** |
| `crafted` | `republique` | oracle ≥ 9,5, **2 types midi** |
| `crafted` | `opera` | oracle ≥ 9,5, **L1–L6** |
| `crafted` | `bastille` | oracle, repos we pairé |
| `crafted` | `nation` | oracle, un senior **0 dîner** |
| `crafted` | `sentier` | oracle, **3 services** (morning) |
| `crafted` | `bourse` | oracle, **2 types midi** sem / sam |
| `crafted` | `madeleine` | oracle, échelle **L1–L6** |
| `crafted` | `concorde` | oracle, 5 fiches juste assez |
| `crafted` | `tuileries` | oracle, **samedi fermé** |
| `crafted` | `palais` | oracle, **lundi fermé** |
| `crafted` | `luxembourg` | oracle, `max_services` serré |
| `crafted` | `odeon` | oracle, 24 h après un soir |
| `crafted` | `montparnasse` | oracle, contrats 8 / 24 / 39 |
| `crafted` | `denfert` | oracle, petits contrats |
| `crafted` | `vaugirard` | oracle, 8–10 fiches, **3 services** |
| `crafted` | `grenelle` | oracle, tentation overqual (grille l’évite) |
| `crafted` | `passy` | oracle, beaucoup d’indispos |
| `crafted` | `auteuil` | oracle, we pair / impair |
| `crafted` | `monceau` | oracle, **deux L6** |
| `crafted` | `pigalle` | oracle, soir tard → **morning** lendemain |
| `crafted` | `abbesses` | oracle, L1–L6 **sans L3** |
| `crafted` | `clichy` | oracle, **3 types** lun–ven / sam / dim |
| `hours` | `mixte` | 8 h / 24 h / 39 h |
| `hours` | `petits` | beaucoup de petits contrats |
| `size` | `studio` | 3 fiches |
| `size` | `grande` | 8–10 fiches, 3 services |
| `overqual` | `cadres` | trop de L5–L6 sur postes bas |
| `closed` | `samedi` | samedi fermé |
| `closed` | `lundi` | lundi fermé |
| `shapes` | `week-we` | 2 types, même service (sem / we) |
| `shapes` | `triple` | 3 types (lun–ven / sam / dim) |
| `shapes` | `journee` | 3 services + 2 types |

`crafted` = planning **d’abord**, contexte **déduit**. Oracle = Manuel. `crafted` : `cycle_score` globale **≥ 9,5** (viser **10**).  
Les 24 non-`crafted` (déjà au catalogue) : manuel **0 interdit** seulement — **on ne les retire pas**, on ne les réécrit pas.  
Les **20** nouveaux sont **tous** `crafted` (pas de diversité-de-forme sans oracle).  
Scan disque. Jeu sans les deux JSON → **omit**, pas 500.  
`engine_ref()` = trim `VERSION` — **`core-3`** après land Core (`engine-seeds.md`). Catalogue 50 **inchangé**.

Parmi les **20** nouveaux : ≥ 4 à 3 services (`morning`) ; ≥ 4 à **2 types ou plus** sur le même `service_id` ; ≥ 4 avec un rôle **level ≥ 6**.  
Méthode **obligatoire** pour chaque nouveau : écrire `expected.json` (grille 14 j) **avant** de figer `context.json` ; `evaluate` → **0 interdit**, **0 hours_miss**, **0 below_role**.

### `context.json`

```
{
  id, category, name, team: "salle", challenge_fr,
  hours: { mode: "services", services: ["morning"?,"midday","evening"], closed_weekdays },
  roles: [{ name, level, team: "salle" }],          # level 1…6 autorisé
  types: [{ id, name, team, service_id, arrivals, departures }],
  typical_week?: [{ weekday, service_id, type_id, closed, team }],
  employees: [{ id, name, role: {name, level, team}, team, contractual_hours_per_week,
                unavailabilities?, wellbeing?, min_shift_hours? }]
}
```

Pas de `invite_token`.  
`typical_week` **absente** : dérivation actuelle (1 type par `(team, service)` — les 7 anciens).  
`typical_week` **présente** : elle gagne ; **une** cellule par `team × service × weekday` ; `type_id` null ssi `closed`. Plusieurs types **peuvent** partager le même `service_id`.  
`hours.services` peut être 2 ou **3** (`morning` autorisé).  
`team_ready(salle)` **vrai**. Cuisine absente.

### `expected.json`

```
{ assignments: [{ employee_id, day_index, weekday, service_id, team, start_minutes, end_minutes, post_level }] }
```

Planning **manuel**. `evaluate` → **0 interdit**. `crafted` (26, dont les 6 déjà là) : `cycle_score` globale **≥ 9,5**. Notes recalculées au run.

## Core

```
engine_ref() -> str            # trim VERSION
list_bench_datasets() -> [ … ]   # ordre : tight, clock, wishes, ladder, crafted, hours, size, overqual, closed, shapes (puis id)
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

Routes run / jobs / datasets **inchangées** (plus `engine_ref` / `app_version` alias sur summaries). `POST all` / `category=crafted` = un job par jeu **listé** (`all` = **50**, `crafted` = **26**).  
Dédup / heartbeat / N workers : **`contracts/domain/worker-queue.md`**.  
Persist : colonne existante `bench_runs.app_version` = `outcome.engine_ref`. Alembic **seulement** `heartbeat_at` + unique partiel jobs (`worker-queue.md`).

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

**Un** Manuel à gauche, puis **une** colonne par `engine_ref`, déclinée en 3 computes (**inverse** de l’ancien : plus de Manuel × 3).

```
Manuel | {engine_ref}                    | {engine_ref} | …
         Minimal | Optimisé | Maximal
```

- **Manuel** : `dataset.manual.global` **une fois**. Clic → compare-chemin `optimized` moteur **courant**.  
- **Chaque cellule modèle × compute** : **uniquement** le delta vs Manuel (`deltas.global`). **Pas** la note absolue. Tiret si pas de run.  
- Clic cellule → `/admin/bench/run/{run_id}` (compare de **ce** run).  
- Couleur delta (globale) : **0 = vert**. Négatif = crescendo **rouge** (clamp −1). Positif = crescendo **bleu** (clamp +1). Tiret = pas de couleur.

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

**`0.37.0`**, note FR : banc, Manuel à gauche, deltas colorés par modèle.

## Tests

HTTP / UI **inchangés** (liste = scan / `list_bench_datasets`).  
Core catalogue : **50** jeux. Les **30** déjà là loadent **bit-à-bit**. Tous les expected : 0 interdit. Les **26** `crafted` : globale ≥ 9,5. Les 20 nouveaux : aussi 0 `hours_miss`, 0 `below_role`.  
≥ 4 des 20 avec `morning` ; ≥ 4 avec 2 `types` le même `service_id` ; ≥ 4 avec un rôle `level >= 6`.  
`engine_ref() == "core-3"` (après land Core). `run_bench(tight, halles, minimal)` vert. Keep-best inchangé. Catalogue 50 inchangé.

## Hors freeze

`weekend-eve` / `eve-first` (moteur). Fills vendored `core-0`/`core-1` sur les nouveaux jeux. Jeux cuisine. CSV/XLSX banc. Archive / sync.
