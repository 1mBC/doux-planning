# Moteur `core-2.5` — réserves (petits contrats / week-end)

Freeze **Core**. Module **nouveau** `engines/core_2_5.py` (copie `core_2.py`). Pas live.

Keep-best **inchangé**. Catalogue 50 **inchangé**.

`engine_ref` = `core-2.5`.

## Pourquoi (manuel vs core-2)

Le manuel **garde** les petits contrats pour le jour où les titulaires se reposent. core-2 les brûle en semaine → trou le week-end.

- **crafted/abbesses** (man 10 vs 9,9) : lun–ven = L6/L5/L2/L1 à 20 h. **Samedi** = les `*b` à 4 h. core-2 pose `l6b` mercredi, `l5b` vendredi en surqual L2 → samedi soir L5 vide.
- **crafted/clichy** (man 10 vs 9,4) : dimanche soir = `gil` (L2, **3 h**). core-2 dimanche soir **vide** (gil pas utilisé là).
- **crafted/luxembourg** : 6 fiches 16 h, max 2 dîners, manuel 0 coupure ; core-2 13 coupures + 1 trou.

## Pipe

```
pour chaque calendrier (off_days) :
  1. fill fewest-first avec skip réserve (ci-dessous)
  2. repair_empty_posts façon 2.2 (+4 h, off_days) — les réserves DEVIENNENT utilisables s’il reste un trou
  3. revert si interdit ↑ OU globale ↓
  4. keep-best
```

Pas de seeds.

## Qui est réserve

`SMALL` = `contractual_hours_per_week <= 8` (strict).  
Ex. abbesses `l6b` 4 h, clichy `gil` 3 h / `els` 4 h.

## Skip réserve pendant le fill

Un `SMALL` est **sauté** sur une fenêtre s’il existe un non-`SMALL` éligible légal (off_days, 11 h, contrat de **ce** non-SMALL, niveau).

Si **aucun** non-SMALL ne peut : on prend le SMALL (sinon trou).

Ça force le samedi abbesses et le dimanche clichy à garder les 4 h / 3 h.

## Repair

Identique 2.2 : les SMALL redeviennent candidats pour les trous restants (le skip fill ne doit pas laisser un trou qu’un SMALL peut tenir).

## SearchTrace

`repairs.mode = "reserve"` + compteurs 2.2.

## Tests

- `crafted/abbesses` optimized : empty == 0, interdit == 0 (manuel 10)
- `crafted/clichy` optimized : empty < 2, interdit == 0, viser empty 0 le dimanche soir
- `crafted/luxembourg` optimized : empty ≤ 1, interdit == 0, globale ≥ core-2
- `crafted/atelier` minimal : pas de régression vs core-2
- pytest vert

## Hors freeze

Seuil 8 h éditable. Live VERSION.
