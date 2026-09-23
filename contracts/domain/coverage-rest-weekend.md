# Fenêtres leftover, repos 11 h, un week-end sur deux

Freeze **domaine**. Core uniquement (evaluate + `coverage.py` + SAT repos).  
UI dictionnaire : brief `ui-coverage-rest-weekend.md` (libellé miss week-end). Infra : rien.

## 1. Personne encore dans le sac après le dernier départ

`remaining_post_levels` = sac **après** le départ (`wizard-ui.md`).  
Si le dernier départ laisse encore des gens dans le sac, ce ne sont pas des postes de durée 0.

Règle :

- Ils restent **aussi longtemps que le sac les liste** (aligné sur le staff : chaque tranche horaire où ils sont encore là).
- Ils ne partent **jamais avant le premier départ** du type.
- Ce n’est **pas** « jusqu’à la fermeture resto » si le sac les a déjà fait partir plus tôt.

Concrètement dans `derive_post_windows` : un poste encore `live` après le dernier événement se termine à `max(dernier événement, premier départ)`. Pas `end = start`.

Exemple LE GARDE MANGER (MIDI) : arrivées L1 10h00, L3 10h30, L2 11h30 ; départs 15h30 sac `[1,3]`, 16h00 sac `[3]`.  
Fenêtres : L2 11h30–15h30, L1 10h00–16h00, L3 **10h30–16h00** (plus 10h30–14h30).  
Tranches : L3 présent de 10h30 à 16h00.

Même chose le soir si le dernier sac n’est pas vide : leftover L3 jusqu’à la dernière horloge de vague (ex. 24h00), pas stretch 4 h → 23h00.

`stretch_to_min_shift` **intouché**. Tous les moteurs lisent `derive_post_windows` : un patch, tous les `engine_ref`.

Tests cuisine qui ferment avec `remaining ()` : inchangés.

## 2. 11 h de repos — seulement les jours qui se suivent

`rest_between_days` : 11 h entre la fin d’une journée travaillée et le début de la **journée travaillée suivante collée** (lundi→mardi, dimanche→lundi, y compris le wrap j13→j0).

S’il y a un jour sans shift au milieu (samedi travaillé, dimanche off, lundi travaillé) : **pas** d’alerte. Le dimanche compte.

Aujourd’hui le wrap cycle applique la formule « jours collés » même s’il y a un trou (NOA samedi B 24h00 → lundi A 10h00 = faux interdit).

Fix `_legal_warnings` : si l’écart de jours est > 1, **sauter** la paire — y compris le wrap.  
`test_cycle_wrap_rest_is_interdit` (dimanche 14h–23h → lundi 8h–16h, écart 1) **reste**.

Copies : `engine.py` **et** chaque `engines/core_*.py` qui vendore evaluate.  
`_rest_between_ok` (placement, jours ±1 seulement) : **intouché**.

## 3. `weekend: every_two` = au moins un week-end off / 14 j.

Gagne sur `wellbeing.md` table Week-end.

| Tenue | Manquée |
|---|---|
| **au moins un** des deux week-ends (sam+dim) entièrement off | les **deux** week-ends ont au moins un shift |

Deux week-ends off = tenu (mieux). Planning vide = tenu.  
`even` / `odd` : inchangés (paire off **et** impaire pas entièrement off, et l’inverse).

Evaluate : miss ssi `not (off_week_0 or off_week_7)`.  
SAT repos : `even_off + odd_off >= 1` (plus `== 1`). Fallback un we off : inchangé.

Copies evaluate + `_build_rest_model` dans `engine.py` et `engines/core_*.py`.

## Tests

- MIDI leftover sac final `[3]` → fenêtre L3 jusqu’à 16h00, tranches avec L3 après 10h30 ; stretch 4 h ne produit pas 14h30.
- Soir leftover sac final `[3]` à 24h00 → L3 jusqu’à 24h00.
- Samedi 24h00 + lundi 10h00, dimanche vide → **pas** `rest_between_days`.
- Dimanche 23h00 + lundi 8h00 → encore `rest_between_days`.
- `every_two` + 0 assignment → pas de miss `weekend_every_two_weeks`.
- `every_two` + les deux we travaillés → miss (inchangé).

Pytest `test_coverage` / `test_engine` / `test_wellbeing` verts. Pas `api/`. Pas `web/` sur la branche Core.

## Hors freeze

Libellé UI « pas exactement un week-end » → brief UI. Fermer un type avec sac vide obligatoire. Archive / sync.
