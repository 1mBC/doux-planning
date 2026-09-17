## Why

Le pipe actuel (SAT repos → fill glouton → keep-best) atteint ses limites :
- Le fill est local, sans vision globale
- Pas de backtrack
- Les compromis multi-axes sont impossibles

Deux approches alternatives :
1. **cp-0** : un seul modèle CP-SAT global avec toutes les contraintes
2. **iter-0** : post-traitement itératif pour améliorer core-5

## What Changes

### cp-0 (nouveau engines/cp_0.py)
- Un seul modèle CP-SAT (OR-Tools) avec toutes les contraintes
- Variables : work[e,d,s], start, end, post_level
- Contraintes dures : repos légal, 11h, 48h, coupure ≤5h, niveau ≥ poste
- Objectif pondéré : postes vides, écart heures, souhaits, sous-rôle, surqual
- Poids : W_empty=1000, W_hours=10, W_wish=50, W_below=5, W_overq=1
- Timeout = SEARCH_SECONDS
- trace.seeder = "cp-sat", solver_status, objective_value, solve_time_ms

### iter-0 (nouveau engines/iter_0.py)
- Pipe : core-5 → repair_loop → keep-best
- 4 passes : swap surqual, balance heures, fill holes, reduce coupures
- Chaque modification validée avant application
- trace.seeder = "iter", base_engine, iterations, improvements

### Registry
- list_engine_refs = core-0 … core-6, cp-0, iter-0
- generate_for dispatch vers le bon module

## Capabilities

### New Capabilities
- `cp-engine`: résolution globale CP-SAT
- `iter-engine`: amélioration itérative post-core-5

## Impact

- `src/doux_planning/engines/cp_0.py` : nouveau module
- `src/doux_planning/engines/iter_0.py` : nouveau module
- `src/doux_planning/engines/registry.py` : ajout cp-0, iter-0
- Tests moteur. Pas de web/, api/, contracts/.
