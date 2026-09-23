# Moteur `iter-0` — post-traitement itératif

Freeze **Core**. Module **nouveau** `engines/iter_0.py`. Pas live (VERSION reste `core-5`).

Keep-best **inchangé** (même `_attempt_key`). Catalogue 50 **inchangé**.

`engine_ref` = `iter-0`.

## Pourquoi

Le fill glouton (`core-5`) pose les shifts un par un sans revenir en arrière. Résultat : des surqualifications évitables, des heures mal réparties.

**`iter-0`** = on part du résultat `core-5`, puis on fait des passes de **réparation** pour améliorer sans casser.

## Pipe

```
1. generate_cycle(core-5)          # fill glouton classique
2. repair_loop(result, max_iter)   # amélioration itérative
3. keep_best(original, repaired)   # garder le meilleur
```

## Passes de réparation

Chaque passe essaie **un type** d'amélioration. On boucle jusqu'à convergence (plus d'amélioration) ou `max_iter` atteint.

### Passe 1 : swap surqual

Pour chaque assignment avec `employee.level > post_level + 1` (surqual ≥ 2) :
- Chercher un autre employé **du même jour** avec `level` plus proche du poste
- Si swap légal (repos, 11h, coupure) et améliore `_attempt_key` → swap

### Passe 2 : balance heures

Pour chaque paire `(e1, e2)` où `|hours[e1] - contract[e1]| > 2` et `|hours[e2] - contract[e2]| > 2` en sens opposé :
- Chercher un shift de `e1` transférable à `e2` (même jour, même service, niveau OK)
- Si transfert légal et rapproche les deux des contrats → transférer

### Passe 3 : fill holes

Pour chaque `empty_post` restant :
- Recalculer les éligibles avec la grille **actuelle** (pas initiale)
- Si un candidat existe maintenant (libéré par les swaps) → poser

### Passe 4 : reduce coupures

Pour chaque employé avec coupure midi+soir le même jour :
- Si un autre employé peut prendre **un** des deux shifts sans créer de coupure → swap
- Priorité : libérer les petits contrats des doubles services

## Paramètres

- `MAX_REPAIR_ITERATIONS = 10` (par passe)
- `MAX_TOTAL_PASSES = 3` (boucle complète)
- Ordre des passes : surqual → heures → holes → coupures

## Légalité

Chaque swap/transfert est **validé** avant application :
- `_can_fill_window` sur le nouvel état
- Vérif 11h, coupure ≤ 5h, max 48h
- Si invalide → skip, essayer le suivant

## SearchTrace (iter-0)

```
{
  seeder: "iter",
  seed_index: 0,
  n_locks: 0,
  calendars_by_seeder: { "iter": 1 },
  calendars_total: 1,
  seeds_infeasible: 0,
  attempt_key: { … },            # calculé sur le result final
  base_engine: "core-5",
  iterations: int,               # nombre total de modifications
  improvements: {
    surqual_swaps: int,
    hour_transfers: int,
    holes_filled: int,
    coupures_reduced: int
  }
}
```

## Registre

Ajouter à `list_engine_refs()` : `iter-0` après `cp-0`.

`generate_for("iter-0", draft, search)` :
1. Appelle `generate_for("core-5", draft, search)` pour le résultat de base
2. Applique `repair_loop`
3. Compare avec `_attempt_key`, garde le meilleur

## Tests

- `list_engine_refs()` inclut `iter-0`.
- `run_bench(tight, halles, minimal, engine_ref="iter-0")` : `attempt_key` ≤ `core-5` (pas pire).
- `run_bench(ladder, jumeaux, optimized, engine_ref="iter-0")` : `overqual` ≤ `core-5`.
- `run_bench(overqual, cadres, minimal, engine_ref="iter-0")` : tourne, `trace.iterations` ≥ 0.
- Un swap illégal n'est **jamais** appliqué.
- Pytest vert.

## Hors freeze

Passes supplémentaires (weekend balance, wish recovery). Heuristiques de sélection. Live VERSION.
