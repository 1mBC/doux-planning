# Brief — coller dans le chat **Core Engine**

Le tech lead : **`core-2.1`** — fill fewest de core-2 + réparation des postes vides. Relis **`contracts/domain/engine-core-2-1.md`** (gagne) + **`engines.md`** (registre mis à jour).

`git pull origin master` ; branche **depuis `master`**.

Nouveau change OpenSpec **`core-2-1-repair`**. Skills → **propose puis apply**. Pas d'archive / sync.

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(core): core-2.1 fill fewest with empty post repair`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés**. VERSION reste `core-5`.

## Comportement

### Module `engines/core_2_1.py`

Basé sur `core_2.py` (copie), avec une **2ème passe** après le fill :

```python
def generate_cycle(draft, search):
    # 1. Fill fewest-first identique à core-2
    result = _fill_cycle(draft, search)
    
    # 2. Si postes vides, tenter de réparer
    empty_count = count_empty_posts(result)
    if empty_count > 0:
        result = repair_empty_posts(draft, result)
    
    return result
```

### repair_empty_posts()

Pour chaque poste vide (ordre fewest du fill initial) :

**Critères de sélection** :
1. Légal dur : niveau ≥ poste, 11h entre shifts, coupure ≤ 5h, max 48h
2. **Tolérance heures** : accepter jusqu'à `+4h` au-delà du contrat sur la semaine (`REPAIR_HOURS_TOLERANCE = 4`)
3. **Tolérance coupure** : accepter une coupure midi+soir (si `max_coupures_per_week` le permet)
4. **Pas de cascade** : le candidat ne crée pas un nouveau poste vide ailleurs

**Tie-break** :
1. Moins de dépassement heures projeté
2. Pas encore de coupure ce jour
3. Moins de surqualification
4. `employee_id`

**Une seule passe** (pas de boucle récursive).

### Registre

- `list_engine_refs()` = `core-0, core-1, core-2, core-2.1, core-3, ...` — **core-2.1 juste après core-2**
- `generate_for("core-2.1", ...)` dispatch vers `engines/core_2_1.generate_cycle`

### SearchTrace

Comme core-2 + champ `repairs` :
```python
trace = {
    "seeder": "empty",
    "seed_index": 0,
    "n_locks": 0,
    "calendars_by_seeder": {"empty": N},
    "calendars_total": N,
    "seeds_infeasible": 0,
    "attempt_key": {...},
    "repairs": {
        "attempted": empty_avant,
        "filled": empty_avant - empty_après,
        "remaining": empty_après
    }
}
```

## Tests

- `list_engine_refs()` inclut `core-2.1` après `core-2`.
- `run_bench(hours, petits, optimized, engine_ref="core-2.1")` : `empty` < 10.
- `run_bench(crafted, pigalle, optimized, engine_ref="core-2.1")` : `empty` < 4.
- `run_bench(crafted, atelier, minimal, engine_ref="core-2.1")` : pas de régression.
- `trace.repairs` présent.
- Contraintes dures **jamais** violées.
- Pytest vert.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core core-2.1 pushed @ <sha>`
