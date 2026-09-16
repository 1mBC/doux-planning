# Banc de jeux (admin)

Freeze **domaine** + HTTP admin. UI = brief UI.  
**Salle only.** Catalogue `data/bench/`.  
Le banc **ne lit / n’écrit jamais** `published_cycles`, `live_sandboxes`, comptes, generate_logs. State **jetable**. Jobs bench ≠ jobs resto (pas de 409 croisé).

## Identité moteur

Un nom par version de moteur : `engine_ref`. **Une** source : `trim(data/bench/VERSION)` (une ligne).  
Ce n’est **pas** le numéro UI (`web/src/release.ts`).

`core-5` = pipe seeds + fill **déjà là aujourd’hui** (`engine-core-5.md`). `core-6` = seeds + recase **seulement les rares** (`engine-core-6.md`). `core-4` = anti-coupure s’il y a le choix. `core-3` = seeds, anti-coupure toujours. `core-2` = fill **fewest** sans seeds. `core-1` = plafonds durs, ordre chrono. `core-0` = avant les plafonds.  
HTTP et rows émettent `engine_ref` **et** `app_version` = **le même string** (alias, une seule source).

Vieux runs `app_version = "0.27.0"` : à la **lecture** `engine_ref = "core-0"` (même moteur). On n’écrit plus `0.27.0`.

Live resto (`POST /v1/generate`) = **`live_engine_ref`** admin (`admin.md`), défaut `VERSION`. Banc : moteurs **vendored** (`engines.md`) — on peut relancer `core-0`…`core-6` sans revert. Le picker **n’affecte pas** le banc (lancer habituel = `VERSION`).

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
`engine_ref()` = trim `VERSION` — **`core-5`** après land Core (`engine-core-5.md`). Catalogue 50 **inchangé**.

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
engine_ref() -> str            # trim VERSION (live)
list_engine_refs() -> [str]    # core-0 … VERSION, ordre chrono
list_bench_datasets() -> [ … ]
load_bench_dataset(category, id) -> BenchDataset
run_bench(category, id, effort, engine_ref: str | None = None) -> BenchOutcome
UnknownBenchDataset
UnknownEngineRef
```

`run_bench` : `engine_ref` omis = `VERSION`. Dispatch `list_engine_refs` → `generate_cycle` figé ou live. Recap ×2 + `deltas` inchangés.  
`BenchOutcome.engine_ref` = le ref **demandé**. `BenchOutcome.trace` = `SearchTrace` (toujours présent).  
**Zéro** `published_cycles`. Keep-best / `SEARCH_*` / pipe seeds **inchangés**. Fill live = `engine-core-5.md`. Tests generate = **`minimal`**.

### Recap unique

```
cycle_recap_from_draft(draft, result) -> CycleRecap
```

Même objet que `cycle_recap` live (`stats`, legal/wish, `facts` miss puis hit, `score` sans resumes).  
`cycle_recap(state, team)` **appelle** ce helper (pas une 2ᵉ formule).  
Banc : `run_bench` l’appelle sur le draft généré **et** sur `expected` (`evaluate` + recap, pas de 2ᵉ solve).  
`BenchOutcome` : `facts` + `expected_facts` = `recap.facts` (liste **complète**, pas seulement evaluate misses). `engine_ref` présent.

## HTTP (admin)

Routes run / jobs / datasets **plus** gaps / batch / export `bank`. `POST all` / `category=crafted` = un job par jeu **listé**, `engine_ref` = **VERSION** (lancer habituel = moteur courant).  
Dédup / heartbeat / batch / N workers : **`contracts/domain/worker-queue.md`**.  
Persist : `bench_runs.app_version` = `outcome.engine_ref` ; JSONB **`trace`**. Alembic : `trace`, jobs `engine_ref` + `batch_id` + `started_at`, unique partiel élargi.

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

Route **déjà là**. 200 = **même forme que compare** + **`trace`** (`SearchTrace` ou `null` si vieux run). 404 si id inconnu.

### GET versions (matrice)

`GET /v1/admin/bench/versions`

```
{
  engine_ref,                    # VERSION courant
  engine_refs: ["core-0", "core-1", "core-2", "core-3", "core-4", "core-5", "core-6"],
  # = list_engine_refs() (registre) ∪ refs déjà en base ; ordre registre puis extras
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
GET /v1/admin/bench/export?scope=bank
```

Bearer admin. 403 / 401 / 503 comme le reste.  
`scope=dataset` sans run → 404. `below_manuel` vide → 200 `{ … datasets: [] }`. `bank` vide → 200 `{ … datasets: [] }`.

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
  scope: "dataset" | "below_manuel" | "bank",
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
          deltas,
          trace                 # SearchTrace ; null si vieux run sans colonne
        }
      ]
    }
  ]
}
```

Ordre datasets = `list_bench_datasets`. Efforts = minimal → optimized → maximal s’ils existent.  
`scope=bank` : **tous** les last-run de **tous** les `engine_ref` (registre), pas seulement VERSION. Un jeu entre s’il a **au moins un** run. Chaque effort d’un ref = une entrée dans `efforts` (tri ref puis effort). `below_manuel` = vs Manuel de ce run. `trace` inclus.  
Fichier UI : `bench-bank.json`.

Pas d’Alembic (recompute) pour dataset / below_manuel. `bank` lit `trace` persisté. Keep-best inchangé.

### POST gaps (trous)

`POST /v1/admin/bench/run` `{ "scope": "gaps" }`

202 :

```
{ batch_id, job_ids, total, status: "queued" }
```

`total` = nombre de jobs **créés ou réutilisés** (dédup). 0 trou → 200 `{ batch_id, job_ids: [], total: 0, status: "done" }` (pas de worker).

Trou = pour chaque `list_bench_datasets` × `{minimal,optimized,maximal}` × `list_engine_refs` :
- pas de last-run, **ou**
- last-run sans `trace` complète (`seeder`, `seed_index`, `n_locks`, `calendars_by_seeder`, `calendars_total`, `seeds_infeasible`, `attempt_key`).

Un job par trou : `(category, dataset_id, search_effort, engine_ref)`. Tous le **même** `batch_id`. File unique, partir = OK.

`POST all` / `category` / `dataset` async : **aussi** un `batch_id` (loader). 202 `{ batch_id, job_ids, total, status: queued }` — `job_ids` **reste**. UI actuelle peut ignorer `batch_id` jusqu’au land UI.

### GET batch / progress

`GET /v1/admin/bench/batches/{batch_id}`  
`GET /v1/admin/bench/batches/active`  → le batch **incomplet** le plus récent, ou 404

200 :

```
{
  batch_id,
  total,
  queued, running, done, failed,
  pct,                 # 100 * (done+failed) / total ; 100 si total=0
  eta_max_seconds      # entier ≥ 0 ; 0 si plus rien à faire
}
```

**Temps max restant** (pessimiste) :

- plafond job = `SEARCH_SECONDS` (3 / 30 / 600) selon `search_effort`
- `n` = max(1, nombre `running` de ce batch)
- `running` : `max(0, plafond − (now − started_at))` ; `started_at` null → plafond plein
- `queued` FIFO `created_at`, round-robin sur `n` workers (charge = restant du running + plafonds suivants)
- `eta_max_seconds` = max des charges

`pct` / eta **ne font qu’avancer** (recalcul poll). 403 / 401 / 503. Batch inconnu → 404.

## UI

Company **`me.admin`**.  
Menu **à plat** : **Historique des computes | Banc | Stats banc**. **Plus** d’entrée Versions. `/admin/bench/versions` → **redirige** vers `/admin/bench`. SPA `/admin/bench/run/{run_id}` inchangé.  
`/admin/bench/stats` = page **Stats banc** (admin). Pas de route HTTP neuve : même `GET /v1/admin/bench/versions`.

**Un seul tableau** (Banc). Source : `GET /v1/admin/bench/versions` (plus le last-run courant seul).

**Un** Manuel à gauche, puis **une** colonne par `engine_ref`. Les 3 computes sont **empilés** dans la cellule (Minimal, Optimisé, Maximal) — plus de sous-colonnes / 2ᵉ ligne d’en-tête.

```
Lancer     | Manuel | {engine_ref} | {engine_ref} | …
  Minimal             Mini
  Optimisé            Opti
  Maximal             Max
  Exporter
```

Colonne **Lancer** (par jeu) : les 3 boutons effort **puis** Exporter, **pile verticale** (plus de wrap horizontal des 3 efforts). Même ordre que les deltas dans la cellule modèle.

- **Manuel** : `dataset.manual.global` **une fois**. Clic → compare-chemin `optimized` moteur **courant**.  
- **Chaque ligne** dans la cellule modèle : delta vs Manuel **en base ×10 entière** (`round(delta_manuel × 10)`, signe `+` / `−`, zéro → `0`). **Pas** de libellé Mini / Opti / Max (l’ordre = Lancer). **Pas** la note absolue. Tiret si pas de run.  
- **À droite** de **cette bulle** (pas dedans) : delta vs le **modèle précédent** de `engine_refs` (même jeu, même effort), **aussi ×10 entière**. Premier `engine_ref` : **pas** d’indicateur. Pas de run précédent **ou round(d×10)=0** : **rien** (plus de liseret vert). Fond de l’indicateur = fond de page.  
  - `> 0` : flèche **haut bleue** + le petit chiffre. Hauteur de flèche et intensité du bleu = crescendo avec `|d|` (échelle **note /10**, clamp **1** — même cap que le fond de la bulle).  
  - `< 0` : flèche **bas rouge** + le petit chiffre. Même crescendo (clamp 1).  
- Clic → `/admin/bench/run/{run_id}`. Clic = bulle + indicateur. **Pas** de contour / bordure / fond autour du couple : la rangée n’a pas de « boîte commune ».  
- **Bulle** = le chiffre vs Manuel, **même chrome qu’avant v0.43** (`.bench-cell` : padding `6px 8px`, bordure `#ddd` radius 6, `font-weight` 650, taille de chiffre **identique**). Fond coloré = delta vs Manuel /10. **0 = vert**. Négatif = rouge clamp 1. Positif = bleu clamp 1. Tiret = pas de bulle. L’indicateur n’est **pas** dans cette boîte et ne réduit **pas** le padding / `font-size` du chiffre.

Sous-titre : `moteur {engine_ref}` = VERSION courant (celui qu’on lance). Pas de bouton revert.

### Recap → page Stats banc

**Plus** de bande Recap (% / min / max des deltas) sur `/admin/bench`. Lien menu **Stats banc**.

`/admin/bench/stats` : titre **Stats banc**, même `AdminNav`, même source `GET /versions`.

**Trois** graphes empilés, **un par compute** (Minimal, Optimisé, Maximal — `effortLabel`). SVG **maison** (pas de lib graphe).

Chaque graphe :

- **X** : `engine_refs` dans l’ordre registre (labels `core-0` …).  
- **Y** : note **globale /10**. `ymax = 10`. `ymin` = `max(0, min_observé − 0,4)` pour que les courbes ne soient pas écrasées en haut. Graduations lisibles (pas 20 ticks).  
- **Trois courbes** sur les notes **absolues** `cell.global` (pas des deltas) :  
  - **Moyenne** — trait plein épais, `#1c1917`  
  - **Min** — tirets, `#c43a3a`  
  - **Max** — trait plein fin, `#2f6fed`  
- Un point par modèle qui a **au moins un** jeu avec `global` non null pour cet effort. Moyenne / min / max = sur **ces** jeux (pas d’intersection forcée avec le modèle d’à côté). Modèle sans run : **pas** de point (la ligne saute).  
- Légende **Moyenne / Min / Max** sous le titre du graphe.  
- Fond clair, axes `#888`, pas de grille dense.

Aucun run pour un compute → graphe masqué (pas un cadre vide).

### Lancer (2 lignes)

Plus une rangée par catégorie.

1. **Global** (inchangé) : « Toutes les catégories » + 3 boutons effort → `scope=all` (moteur **courant**).  
2. **Par compute** : 3 contrôles (Minimal / Optimisé / Maximal) → catégories → `scope=category`.  
3. **Compléter les trous** : `scope=gaps`. Un clic, **une** pile (Minimal + Opti + Maximal × tous les refs). Quitter la page = OK.

Loader **inline sous le titre « Lancer »** (pas d’overlay, **pas** de flou sur la page) dès qu’un batch est actif (`GET …/batches/active` au mount + après un lancer lot / gaps) :

- **%** = `pct`  
- **temps max restant** = `eta_max_seconds` formaté (ex. `~ 12 min`)  
Poll ~2 s jusqu’à `pct == 100` puis refresh versions. Tableau / Stats / export **restent utilisables**. Le overlay `calc-overlay` du planning resto **ne s’applique pas** au Banc. Pas besoin de rester sur la page pour que ça tourne.

Export : **Exporter tout le banc** → `scope=bank` (`bench-bank.json`) en plus des deux exports existants.

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

**`0.45.0`**, note FR : bulle delta comme avant, plus de trait vert à zéro.

## Tests

HTTP / UI **inchangés** (liste = scan / `list_bench_datasets`).  
Core catalogue : **50** jeux. Les **30** déjà là loadent **bit-à-bit**. Tous les expected : 0 interdit. Les **26** `crafted` : globale ≥ 9,5. Les 20 nouveaux : aussi 0 `hours_miss`, 0 `below_role`.  
≥ 4 des 20 avec `morning` ; ≥ 4 avec 2 `types` le même `service_id` ; ≥ 4 avec un rôle `level >= 6`.  
`engine_ref() == "core-5"`. `list_engine_refs()` = `core-0`…`core-6`. `run_bench(tight, halles, minimal)` et `run_bench(..., engine_ref="core-4"|"core-6")` verts + `trace`. Keep-best inchangé. Catalogue 50 inchangé.

## Hors freeze

`weekend-eve` / `eve-first` (moteur). Relance **globale** (écraser les runs complets). Jeux cuisine. CSV/XLSX banc. Archive / sync.
