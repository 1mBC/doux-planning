# Moteur `core-2.4` — ouvreurs / fermeurs (11 h)

Freeze **Core**. Module **nouveau** `engines/core_2_4.py` (copie `core_2.py`). Pas live.

Keep-best **inchangé**. Catalogue 50 **inchangé**.

`engine_ref` = `core-2.4`.

## Pourquoi (manuel vs core-2)

Le manuel **sépare** ceux qui ferment et ceux qui ouvrent. core-2 enchaîne soir tard → trou le lendemain (11 h) ou pose un interdit `rest_between_days`.

- **crafted/pigalle** (man 10 vs 9,3) : `nox`/`nyx` ferment, `aub`/`dawn` ouvrent, `mid`/`noon` midi. Jamais la même fiche soir+morning. core-2 : `noon` midi+soir jeudi → vendredi soir vide, samedi midi+soir vides.
- **crafted/odeon** : manuel 0 coupure, 12 h pile ; core-2 8 coupures + 1 trou.
- **crafted/vaugirard** (man 10 vs 9,9) : 0 trou mais **2 interdits 11 h**. Manuel : une fiche = un service (morning / midi / soir), jamais deux.

## Pipe

```
pour chaque calendrier (off_days) :
  1. fill fewest-first (core-2)
  2. break_11h(assignments, off_days)
  3. si empty > 0 : repair_empty_posts façon 2.2 (+4 h, off_days)
  4. revert si interdit ↑ OU globale ↓
  5. keep-best
```

Pas de seeds.

## break_11h

Pour chaque paire qui casse (ou bloquerait) la 11 h : soir **jour D** qui finit tard + morning **jour D+1** de la même fiche.

1. Si morning D+1 est **vide** à cause de ce soir : **déplacer** le soir D vers un autre éligible (off_days, 11 h, 48 h, niveau, pas d’overlap). Puis poser le morning.
2. Si les deux sont posés et `rest_between_days` interdit : déplacer **l’un** des deux (préférer déplacer le soir, moins de vagues le morning).
3. Ne jamais créer un **nouveau** poste vide.
4. Ne pas poser sur un jour `off_days`.

Puis repair 2.2 sur les trous encore là (pigalle : une fois les fermeurs libérés, le fill-trou +4 h suffit).

## SearchTrace

`repairs`: `{ attempted, filled, remaining, displaced_11h }` + `mode = "open_close"`.

## Tests

- `crafted/pigalle` optimized : empty < 4, interdit == 0, globale ≥ core-2
- `crafted/vaugirard` optimized : `interdit` == 0 (les 2 `rest_between_days` de core-2)
- `crafted/odeon` optimized : empty ≤ 1, interdit == 0
- `ladder/jumeaux` optimized : interdit == 0
- pytest vert

## Hors freeze

Bandes horaires configurables. Live VERSION.
