# Moteur `core-2.1` — fill fewest + réparation postes vides

Freeze **Core**. Module **nouveau** `engines/core_2_1.py`. Pas live (VERSION reste `core-5`).

Keep-best **inchangé** (même `_attempt_key`). Catalogue 50 **inchangé**.

`engine_ref` = `core-2.1`.

## Pourquoi

core-2 est le meilleur moteur actuel sur le banc, mais il laisse des postes vides sur certains jeux :
- **hours/petits** : 10 postes vides (petits contrats, pas assez d'heures)
- **crafted/pigalle** : 4 postes vides (soir tard → morning, contrainte 11h)
- **crafted/clichy/republique** : 2 postes vides (types multiples)

iter-0 montre qu'on peut remplir ces postes en acceptant plus de dépassement d'heures. core-2.1 applique cette idée de façon **ciblée** après le fill initial.

## Pipe

```
1. fill fewest-first (identique à core-2)
2. si empty > 0 : repair_empty_posts()
3. keep-best sur les calendriers (identique à core-2)
```

**Pas de seeds** (comme core-2). Pas d'anti-coupure. Ordre fewest-first conservé.

## repair_empty_posts()

Pour chaque poste vide (dans l'ordre fewest du fill initial) :

### Critères de sélection d'un candidat

1. **Légal dur** : niveau ≥ poste, 11h entre shifts, coupure ≤ 5h, max 48h
2. **Tolérance heures** : accepter jusqu'à `+4h` au-delà du contrat sur la semaine
3. **Tolérance coupure** : accepter une coupure midi+soir le même jour (si le plafond `max_coupures_per_week` le permet)
4. **Pas de cascade** : le candidat ne doit pas créer un nouveau poste vide ailleurs (il n'était pas seul éligible sur un autre créneau)

### Ordre de préférence (tie-break)

1. Celui qui a le **moins** de dépassement d'heures projeté
2. Celui qui **n'a pas** encore de coupure ce jour
3. Celui avec le **moins** de surqualification
4. `employee_id`

### Application

- Si un candidat est trouvé → poser le shift
- Si aucun candidat → le poste reste vide (on ne casse pas les durs)
- **Une seule passe** (pas de boucle récursive)

## Paramètres

```python
REPAIR_HOURS_TOLERANCE = 4  # heures au-delà du contrat acceptées
```

## SearchTrace (core-2.1)

```
{
  seeder: "empty",
  seed_index: 0,
  n_locks: 0,
  calendars_by_seeder: { "empty": N },
  calendars_total: N,
  seeds_infeasible: 0,
  attempt_key: { … },
  repairs: {
    attempted: int,      # postes vides avant repair
    filled: int,         # postes remplis par repair
    remaining: int       # postes encore vides après
  }
}
```

## Registre

Insérer `core-2.1` **juste après** `core-2` dans `list_engine_refs()` :

```
core-0, core-1, core-2, core-2.1, core-3, core-4, core-5, core-6, cp-0, iter-0
```

`generate_for("core-2.1", draft, search)` → appelle `engines/core_2_1.generate_cycle`.

## Tests

- `list_engine_refs()` inclut `core-2.1` après `core-2`.
- `run_bench(hours, petits, optimized, engine_ref="core-2.1")` : `empty` < 10 (amélioration vs core-2).
- `run_bench(crafted, pigalle, optimized, engine_ref="core-2.1")` : `empty` < 4.
- `run_bench(crafted, atelier, minimal, engine_ref="core-2.1")` : pas de régression vs core-2 (jeu déjà bon).
- `trace.repairs` présent avec les compteurs.
- Contraintes dures **jamais** violées par la réparation.
- Pytest vert.

## Hors freeze

Tuning `REPAIR_HOURS_TOLERANCE`. Réparation multi-passes. Live VERSION.
