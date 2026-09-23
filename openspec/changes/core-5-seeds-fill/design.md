## Architecture

Deux nouveaux modules : `core_4.py` (snapshot) et `core_6.py` (nouveau).

## Approach

### core-5 fill (engine.py)

Dans `_soft_penalty`, remplacer :
```python
creates_coupure = _creates_coupure(assignments, trial) if coupure_matters else False
return (... int(creates_coupure) ...)
```
Par :
```python
started_day = _already_on_day(assignments, employee.id, trial.day_index)
return (... int(not started_day) ...)
```

Retirer le paramètre `coupure_matters`.

Dans `_pick_for_post`, simplifier : supprimer la collecte `candidates` avec `creates_coupure` et `has_choice`, revenir au scoring direct comme core-2.

### core-6 fill (engines/core_6.py)

Copie de engine.py avec modifications du fill :

1. Nouvelle fonction `_is_rare(draft, assignments, employee, employee_pool, off_days)` :
   - Parcourt toutes les fenêtres vides du cycle (même équipe)
   - Pour chaque fenêtre, compte les fiches qui `_can_fill_window`
   - Si le candidat peut la remplir ET ≤ 3 éligibles → candidat rare

2. Dans `_soft_penalty`, composant coupure/recase :
   - Ajouter paramètre `is_rare: bool = False`
   - Si rare → `int(not started_day)`
   - Sinon → `int(creates_coupure)`

3. Dans `_pick_for_post`, calculer `is_rare` pour chaque candidat et le passer à `_soft_penalty`.

### Registry

- `ENGINE_REFS = ("core-0", ..., "core-6")`
- `_FROZEN` : ajouter core_4, core_6
- `generate_for` : core-5 = live, core-3/core-4/core-6 utilisent `result.trace` (pas stub)

### generate_team

Ajouter paramètre `engine_ref: str | None = None`. Si fourni, utilise `generate_for`; sinon, `generate_cycle` (VERSION).

## Risks

- core-6 `_is_rare` peut être coûteux si beaucoup de fenêtres. Limiter aux fenêtres du même jour ou optimiser si nécessaire.
