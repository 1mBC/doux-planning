## Architecture

Pas de nouveau module. Le fill existant dans `engine.py` est adapté.

## Approach

### Fill — coupure s'il y a le choix

Dans `_pick_for_post`, après avoir collecté tous les candidats légaux (hard-skips passés, `penalty[0] == 0`), on détermine si au moins un candidat ne créerait pas de coupure.

1. Parcourir tous les employés éligibles, construire les `trial` shifts.
2. Pour chaque candidat qui passe les hard-skips : stocker `(employee, assigned, creates_coupure)`.
3. Après la boucle : `has_choice = any(not c for _, _, c in candidates)`.
4. Re-scorer chaque candidat avec le bon composant coupure :
   - Si `has_choice` : `int(creates_coupure)` comme avant.
   - Sinon : `0` (pas de pénalité coupure).
5. Trier et retourner le meilleur.

### `_soft_penalty` — paramètre optionnel

Ajouter un paramètre `coupure_matters: bool = True` à `_soft_penalty`. Quand `False`, le composant coupure vaut `0` quoi qu'il arrive.

### Snapshot et registre

- Copier `engine.py` vers `engines/core_3.py` en changeant les imports relatifs si nécessaire.
- Dans `registry.py` : ajouter `"core-3"` dans `_FROZEN` pointant vers `core_3` module, ajouter `"core-4"` dans `ENGINE_REFS`, et faire pointer `"core-4"` vers le live `generate_cycle`.
- Mettre `data/bench/VERSION` à `core-4`.

## Risks

- Les tests de régression doivent confirmer que le comportement n'est pas cassé pour les jeux où des alternatives existent.
- Le banc `run_bench(tight, halles, minimal)` valide l'intégration.

## Alternatives Considered

- Modifier `_soft_penalty` globalement avec un flag au niveau du module : rejeté car moins explicite.
- Passer l'info via le draft : non nécessaire, le contexte est local à `_pick_for_post`.
