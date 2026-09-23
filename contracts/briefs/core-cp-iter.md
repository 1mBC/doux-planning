# Brief — coller dans le chat **Core Engine**

Le tech lead : **`cp-0` + `iter-0`** — deux nouveaux moteurs en parallèle. Relis **`contracts/domain/engine-cp-0.md`** + **`engine-iter-0.md`** + **`engines.md`** (registre mis à jour).

`git pull origin master` ; branche **depuis `master`**.

Nouveau change OpenSpec **`cp-iter-engines`** (les deux moteurs dans **un** change). Skills → **propose puis apply**. Pas d'archive / sync.

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(core): cp-0 CP-SAT global and iter-0 iterative repair`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés** (même formule). VERSION reste `core-5`.

## Comportement

### `cp-0` — CP-SAT global (OR-Tools)

- Module **nouveau** `engines/cp_0.py`
- Un seul modèle CP-SAT avec **toutes** les contraintes (pas seulement repos)
- Variables : `work[e,d,s]`, `start`, `end`, `post_level`
- Contraintes dures : repos légal, 11h, 48h, coupure ≤5h, niveau ≥ poste, max_services dur
- Objectif : minimiser `W_empty * postes_vides + W_hours * écart_heures + W_wish * souhaits_cassés + W_below * sous_rôle + W_overq * surqual`
- Poids initiaux : `W_empty=1000, W_hours=10, W_wish=50, W_below=5, W_overq=1`
- Timeout = `SEARCH_SECONDS` de l'effort
- `trace.seeder = "cp-sat"`, `trace.solver_status`, `trace.objective_value`, `trace.solve_time_ms`

### `iter-0` — post-traitement itératif

- Module **nouveau** `engines/iter_0.py`
- Pipe : `core-5` → `repair_loop` → keep-best
- 4 passes de réparation (boucle jusqu'à convergence ou max 3 tours) :
  1. **swap surqual** : échanger un L6 sur poste L1 avec un L2 du même jour
  2. **balance heures** : transférer un shift pour rapprocher des contrats
  3. **fill holes** : re-tenter les postes vides avec la grille mise à jour
  4. **reduce coupures** : libérer les petits contrats des doubles services
- Chaque modification est **validée** (légalité) avant application
- `trace.seeder = "iter"`, `trace.base_engine = "core-5"`, `trace.iterations`, `trace.improvements`

### Registre

- `list_engine_refs()` = `core-0` … `core-6`, `cp-0`, `iter-0`
- `generate_for("cp-0"|"iter-0", draft, search)` dispatch vers le bon module

## Tests

`list_engine_refs()` inclut `cp-0` et `iter-0`.

**cp-0** :
- `run_bench(tight, halles, minimal, engine_ref="cp-0")` : 0 interdit, `trace.seeder == "cp-sat"`
- `run_bench(ladder, jumeaux, optimized, engine_ref="cp-0")` : compare vs core-5
- Timeout respecté (pas de hang)

**iter-0** :
- `run_bench(tight, halles, minimal, engine_ref="iter-0")` : `attempt_key` ≤ core-5
- `run_bench(ladder, jumeaux, optimized, engine_ref="iter-0")` : `overqual` ≤ core-5
- Un swap illégal n'est jamais appliqué

Pytest moteur verts. 50 jeux loadent.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core cp-0+iter-0 pushed @ <sha>`
