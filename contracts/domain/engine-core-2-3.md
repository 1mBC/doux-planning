# Moteur `core-2.3` — titulaires jusqu’à 48 h légales

Freeze **Core**. Module **nouveau** `engines/core_2_3.py` (copie `core_2.py`, pas 2.1). Pas live (VERSION reste `core-5`).

Keep-best **inchangé**. Catalogue 50 **inchangé**.

`engine_ref` = `core-2.3`.

## Pourquoi (manuel vs core-2, export 3)

Là où le manuel **gagne** core-2, il ne répartit pas les heures : il **empile** sur 1–2 titulaires, jusqu’à ~40 h, **sous le plafond légal 48 h**, 2 repos tenus, et laisse des fiches sur le banc.

- **hours/petits** (man 8,4 vs core-2 7,1) : 6 contrats 8 h, 4 postes/jour. Manuel : `a` et `c` à **40 h**, deux fiches à 8 h, **deux à 0 h**. 0 trou, 0 interdit. core-2 étale sur tout le monde → 10 trous. 2.1 +4 h → 8 trous et globale **pire** (contrat à 0).
- **shapes/triple** dimanche : manuel `marc` midi+soir ; core-2 dimanche **vide**.
- **crafted/republique** samedi soir : manuel les 17 h (`b`+`d`) en double service ; core-2 soir vide.
- **crafted/opera** samedi L6 : le manuel met un L5 sur L6 (sous-rôle — le fill **interdit** ça). Autre voie légale : **heures en plus** sur le L6 (`dir` 20 h → 24 h).

Ce n’est **pas** voler un repos (les manuels : 0 semaine à < 2 repos). C’est **ignorer le contrat comme plafond de fill** dès qu’un poste resterait vide.

## Pipe

```
pour chaque calendrier (off_days) :
  1. fill fewest-first (core-2) — skip contrat inchangé tant qu’un collègue est sous contrat
  2. repair_titular(assignments, off_days)   # cap = 48 h légales, pas contrat+4
  3. revert si interdit ↑ OU globale ↓
  4. keep-best
```

Pas de seeds.

## repair_titular

Comme `repair_empty_posts` de 2.2, **sauf** :

1. Plafond heures = `MAX_WEEKLY_HOURS` (48 h), **pas** contrat+4
2. Tie-break **concentrer** (comme le manuel) :
   1. déjà un shift **ce jour** (coupure OK si plafond fiche)
   2. **plus** d’heures déjà posées cette semaine (titulaire)
   3. moins de surqual
   4. `employee_id`
3. Repos SAT / 11 h / 48 h / max_services / cascade / indispo : identiques 2.2
4. Une passe

## SearchTrace

Même forme que 2.2 + `repairs.mode = "titular48"`.

## Tests

- registre après `core-2.2`
- `hours/petits` optimized : `empty` < 10, `interdit` == 0, globale ≥ core-2. Viser empty **0** (manuel).
- `shapes/triple` optimized : empty < 4, interdit == 0
- `crafted/republique` optimized : empty < 2, interdit == 0
- `tight/marche` optimized : interdit == 0 (ne pas copier 2.1)
- pytest vert

## Hors freeze

Choisir *quels* titulaires (L2 vs L1). Live VERSION.
