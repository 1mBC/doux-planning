# Moteur `cp-0` — CP-SAT global

Freeze **Core**. Module **nouveau** `engines/cp_0.py`. Pas live (VERSION reste `core-5`).

Keep-best **inchangé** (même `_attempt_key`). Catalogue 50 **inchangé**.

`engine_ref` = `cp-0`.

## Pourquoi

Le pipe actuel (SAT repos → fill glouton → keep-best) atteint ses limites :
- Le fill est local (créneau par créneau), sans vision globale
- Pas de backtrack : une mauvaise décision tôt bloque la suite
- Les compromis multi-axes sont impossibles (tuple lexicographique)

**`cp-0`** = un seul modèle CP-SAT (OR-Tools) qui intègre **toutes** les contraintes, pas seulement les repos.

## Modèle CP-SAT

### Variables

Pour chaque `(employee, day_index, service_id)` :
- `work[e, d, s]` : BoolVar — employé `e` travaille le service `s` du jour `d`
- `start[e, d, s]` : IntVar — minute de début (si `work` = 1)
- `end[e, d, s]` : IntVar — minute de fin (si `work` = 1)
- `post_level[e, d, s]` : IntVar — niveau du poste tenu (si `work` = 1)

### Contraintes dures (infaisable si violée)

1. **Repos légal** : `work[e, d, *]` = 0 pour au moins 2 jours par semaine (j0–6, j7–13)
2. **11h entre shifts** : si `work[e, d, s1]` et `work[e, d+1, s2]`, alors `start[e, d+1, s2] - end[e, d, s1] >= 660` minutes
3. **Max 48h / semaine** : `Σ duration[e, d, s]` sur une semaine ≤ 2880 minutes
4. **Coupure ≤ 5h** : si deux shifts le même jour, gap ≤ 300 minutes
5. **Niveau ≥ poste** : `employee.level >= post_level[e, d, s]`
6. **Max services dur** : si `wellbeing.max_services.evening = 0`, alors `Σ work[e, *, evening]` = 0

### Contraintes souples (objectif)

Objectif = **minimiser** une somme pondérée :

```
minimize:
  W_empty   * Σ empty_post[d, s, p]           # postes vides
+ W_hours   * Σ |hours[e] - contract[e]|      # écart heures
+ W_wish    * Σ wish_broken[e, w]             # souhaits non tenus
+ W_below   * Σ max(0, post_level - 1)        # sous-rôle potentiel
+ W_overq   * Σ (employee.level - post_level) # surqualification
```

**Poids initiaux** (à ajuster sur le banc) :
- `W_empty = 1000` (un poste vide coûte cher)
- `W_hours = 10` (par heure d'écart)
- `W_wish = 50` (par souhait cassé)
- `W_below = 5` (par niveau de sous-rôle)
- `W_overq = 1` (par niveau de surqual)

### Couverture

Pour chaque fenêtre `(day_index, service_id, arrival_wave)` avec `post_levels` requis :
- Variable `filled[d, s, w, i]` = 1 ssi le poste `i` de cette vague est tenu
- Contrainte : `Σ work[e, d, s] where level >= required` >= nb postes requis, **ou** `empty_post` += 1

### Solve

- Timeout = `SEARCH_SECONDS` de l'effort (`minimal` 3s, `optimized` 30s, `maximal` 600s)
- **Un seul** solve (pas de keep-best sur N calendriers)
- Si INFEASIBLE : retourner le meilleur partiel trouvé, avec `trace.solver_status = "infeasible"`
- Si OPTIMAL ou FEASIBLE : extraire les assignments

### SearchTrace (cp-0)

```
{
  seeder: "cp-sat",
  seed_index: 0,
  n_locks: 0,
  calendars_by_seeder: { "cp-sat": 1 },
  calendars_total: 1,
  seeds_infeasible: 0,
  attempt_key: { … },            # calculé sur le result
  solver_status: "optimal" | "feasible" | "infeasible",
  objective_value: int | null,
  solve_time_ms: int
}
```

## Registre

Ajouter à `list_engine_refs()` : `cp-0` après `core-6`.

`generate_for("cp-0", draft, search)` → appelle `engines/cp_0.generate_cycle`.

## Tests

- `list_engine_refs()` inclut `cp-0`.
- `run_bench(tight, halles, minimal, engine_ref="cp-0")` : 0 interdit expected, `trace.seeder == "cp-sat"`.
- `run_bench(ladder, jumeaux, optimized, engine_ref="cp-0")` : compare vs `core-5` (objectif = moins de surqual à couverture égale).
- `run_bench(overqual, cadres, minimal, engine_ref="cp-0")` : tourne sans crash.
- Timeout respecté (pas de hang).
- Pytest vert.

## Hors freeze

Tuning des poids. Warm-start depuis core-5. Hints. Symétrie breaking. Live VERSION.
