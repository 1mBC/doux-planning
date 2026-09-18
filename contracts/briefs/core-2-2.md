# Brief — coller dans le chat **Core Engine**

Le tech lead : **`core-2.2`** — même idée que 2.1 (boucher les postes vides après le fill fewest), **sans voler le 2e jour de repos**. Relis **`contracts/domain/engine-core-2-2.md`** (gagne) + **`engines.md`**.

`git pull origin master` ; branche **depuis `master`**.

Nouveau change OpenSpec **`core-2-2-legal-repair`**. Skills → **propose puis apply**. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(core): core-2.2 legal empty-post repair`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés**. VERSION reste `core-5`.

## Comportement

Module **nouveau** `engines/core_2_2.py`, copie de `core_2.py` (pas de `core_2_1.py`).

### Pipe (dans `consider(off_days)`, pas après keep-best)

```
assignments = fill fewest-first (core-2, avec off_days)
si empty > 0:
    repaired = repair_empty_posts(assignments, off_days)
    si interdit(repaired) > interdit(fill) : garder le fill
    sinon : repaired
keep-best
```

**Bug 2.1 à ne pas recopier** : 2.1 répare le gagnant **sans** `off_days` → pose sur un jour de repos SAT (`weekly_rest_days`). 2.2 passe **toujours** `off_days`.

### repair_empty_posts

Pour chaque poste vide, candidat OK ssi :

1. `day_index not in off_days[employee]`
2. durs : niveau, 11 h, coupure ≤ 5 h, 48 h, `max_services`, overlap, indispo
3. heures ≤ contrat + 4
4. coupure si plafond `max_coupures_per_week` OK
5. pas seul éligible restant sur un autre poste encore vide

Tie-break : overage heures, coupure du jour, surqual, `employee_id`. Une passe.

### SearchTrace

`repairs` **à la racine** (`SearchTrace.repairs`), **pas** dans `attempt_key`.  
Étendre `SearchTrace` live (`engine.py`) : `repairs: dict | None = None`.  
`registry.py` : insérer `core-2.2` après `core-2.1`, copier `repairs` dans `generate_for`.

### Tests (minimum)

- registre : `core-2.2` juste après `core-2.1`
- `crafted/pigalle` optimized : empty < 4, interdit == 0
- `tight/marche` optimized : interdit == 0
- `ladder/jumeaux` optimized : interdit == 0
- `crafted/atelier` minimal : pas pire que core-2
- pytest vert
