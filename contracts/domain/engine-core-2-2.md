# Moteur `core-2.2` — fill fewest + réparation **légale** des postes vides

Freeze **Core**. Module **nouveau** `engines/core_2_2.py`. Pas live (VERSION reste `core-5`).

Keep-best **inchangé** (même `_attempt_key`). Catalogue 50 **inchangé**.

`engine_ref` = `core-2.2`.

## Pourquoi (constat banc, export 3)

`core-2` reste le meilleur **légal** sur la moyenne. `core-2.1` bouche plus de trous (empty moyen 0,92 → 0,34 en optimized) **mais** crée des **interdits** `weekly_rest_days` : la réparation pose un shift sur un jour de repos SAT (2e repos volé). Keep-best met `empty` **avant** `interdit`, donc 2.1 **garde** ces plannings illégaux.

Exemples 2.1 optimized : `tight/marche` empty 4→0 mais interdit 0→4 ; toute la famille `ladder/*` idem.  
Exemples 2.1 **légaux** (à conserver) : `crafted/pigalle` empty 4→0 interdit 0 ; `odeon` / `republique` / `nation`.

**`core-2.2`** = la réparation de 2.1 **faite comme le spec 2.1 le disait** : jamais casser un dur, en particulier les 2 repos / semaine déjà posés par le SAT.

## Pipe

```
pour chaque calendrier de repos (off_days) :
  1. fill fewest-first (identique à core-2)
  2. si empty > 0 : repair_empty_posts(assignments, off_days)
  3. si interdit(repaired) > interdit(pre-repair) : revert (garder le fill)
  4. keep-best (identique à core-2)
```

**Pas de seeds.** Pas d’anti-coupure de fill. Ordre fewest-first conservé.

**Différence vs 2.1 (bug)** : 2.1 répare **après** keep-best, **sans** `off_days` → pose sur un jour de repos. 2.2 répare **dans** `consider()`, avec le `off_days` de **ce** calendrier.

## repair_empty_posts(assignments, off_days)

Pour chaque poste vide (ordre fewest du fill, comme 2.1) :

### Critères (tous obligatoires)

1. **Repos SAT** : `day_index` **pas** dans `off_days[employee]` (c’est le check manquant de 2.1)
2. **Légal dur** : niveau ≥ poste, 11 h entre shifts, coupure ≤ 5 h, max 48 h / semaine, `max_services` dur, pas d’overlap, pas d’indispo
3. **Tolérance heures** : jusqu’à `+4 h` au-delà du contrat sur la semaine (`REPAIR_HOURS_TOLERANCE = 4`)
4. **Tolérance coupure** : une coupure midi+soir autorisée si `max_coupures_per_week` le permet
5. **Pas de cascade** : le candidat n’est pas le **seul** éligible restant sur un **autre** poste encore vide (éligibilité = `_can_fill_window` sur l’état courant + `off_days`)

### Tie-break (identique 2.1)

1. Moins de dépassement d’heures projeté
2. Pas encore de coupure ce jour
3. Moins de surqualification
4. `employee_id`

### Application

- Candidat trouvé → poser
- Aucun → le poste reste vide
- **Une passe** par calendrier (pas de boucle récursive)
- Filet : si `evaluate` après repair a **plus** d’interdit que avant → revert ce calendrier

## SearchTrace (core-2.2)

```
{
  seeder: "empty",
  seed_index: 0,
  n_locks: 0,
  calendars_by_seeder: { "empty": N },
  calendars_total: N,
  seeds_infeasible: 0,
  attempt_key: { empty, interdit, hours_miss, souhait, below_role, overqual },
  repairs: {
    attempted: int,       # empty du fill gagnant, avant repair
    filled: int,
    remaining: int,
    skipped_illegal: int  # candidats rejetés pour off_days / durs
  }
}
```

`attempt_key` = **uniquement** les 6 clés keep-best (pas de `repairs` dedans — 2.1 les avait nichés là).  
`SearchTrace` live (`engine.py`) : ajouter `repairs: dict | None = None` (défaut None, les autres moteurs inchangés). `registry.generate_for` **copie** `repairs` (ne pas le drop).

## Registre

Insérer `core-2.2` **juste après** `core-2.1` :

```
core-0, core-1, core-2, core-2.1, core-2.2, core-3, core-4, core-5, core-6, cp-0, iter-0
```

`generate_for("core-2.2", …)` → `engines/core_2_2.generate_cycle`.  
`_CUSTOM_TRACE_ENGINES` inclut `core-2.2`.

## Tests

- `list_engine_refs()` inclut `core-2.2` après `core-2.1`.
- `run_bench(crafted, pigalle, optimized, engine_ref="core-2.2")` : `empty` < 4 **et** `interdit` == 0.
- `run_bench(tight, marche, optimized, engine_ref="core-2.2")` : `interdit` == 0 (ne pas copier 2.1).
- `run_bench(ladder, jumeaux, optimized, engine_ref="core-2.2")` : `interdit` == 0.
- `run_bench(crafted, atelier, minimal, engine_ref="core-2.2")` : pas de régression vs core-2 (globale, empty, interdit).
- `trace.repairs` présent **à la racine** du trace (pas dans `attempt_key`).
- Contraintes dures **jamais** violées par la réparation.
- Pytest vert.

## Hors freeze

Tuning `REPAIR_HOURS_TOLERANCE`. Multi-passes. `core-2.3` (swaps surqual sans toucher empty). Live VERSION.
