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

`run_bench` inchangé : copie jetable + `generate_cycle` + `cycle_score` ×2 + `deltas` (Modèle − Manuel).  
**Zéro** `published_cycles`. Keep-best / `SEARCH_*` inchangés. Tests generate = **`minimal`**.  
Serialize **facts** misses evaluate (payload, pas `message`) sur `bench_runs` — plus `warnings[].message`. Score **sans** `resumes`. Compare UI = dictionnaire `score-facts.md`.

## HTTP (admin)

Inchangé (`bench.md` tranche 31). `POST all` / `category=crafted` = **un job par jeu** (7 si all).  
SPA déjà `/admin`, `/admin/bench`, `/admin/bench/{category}/{dataset_id}/{search_effort}`.

## UI

Company **`me.admin`**.

**Menu admin** (les deux pages `/admin` et `/admin/bench`) — plus de bouton isolé « Banc » / « ← Admin » :

```
Historique des computes | Banc
```

`/admin` = historique (log generate, inchangé). `/admin/bench` = banc. L’entrée courante est marquée (pas un 2ᵉ clic utile). Compare : le même menu au-dessus.

**Tableau banc** : une ligne par jeu. Pour **chaque** effort, **3 sous-colonnes** :

| Modèle | Manuel | Delta |
|---|---|---|
| `score.global` | `expected_score.global` | `deltas.global` |

Tiret si pas de run. Clic sur la cellule (ou la ligne d’effort) → compare.  
Libellés **Modèle** / **Manuel** / **Delta** (pas « oracle », pas « généré »). Manuel = planning fichier ; plus tard restos réels.

Page compare : titre inchangé. Blocs **Modèle** puis **Manuel** (notes + grilles). Pas d’édition.

Lancer all | catégorie | jeu × 3 efforts : inchangé.

**`0.29.0`**, note FR : menu admin + banc Modèle / Manuel / Delta + 3 crafted.

## Tests

Core : 7 jeux listés (4 + atelier/rivoli/marais). `evaluate` expected 0 interdit. `crafted` : globale Manuel ≥ 9,5. `run_bench` halles minimal inchangé.  
Infra : POST all maximal → **7** jobs / 7 runs (tick stub). 403 non-admin.  
UI : menu 2 entrées ; tableau sous-colonnes ; barre v0.29.0.

## Hors freeze

Dashboard historique. `engine_ref`. Jeux cuisine. Rewrite Saint-Cloud. Archive / sync.
