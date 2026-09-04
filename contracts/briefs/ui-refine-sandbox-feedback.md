# Brief — coller dans le chat **UI** (suite)

Le tech lead : retours overlay. **Uniquement `web/`.** Pas de Core, pas d’Infra, pas de score inventé, pas d’archive / commit.

## 1. Plus de bloc score

Retirer `ScoreCompare` (vides / interdits / heures / souhaits / sous-rôle / surqualif. avant → après) des **trois** gestes. Même les lignes qui bougent (ex. heures 78 → 77,75) : c’est du bruit, l’`impact` suffit. Continuer à parser `current_score` / `trial_score` / `score` si l’API les envoie, **ne plus les afficher** dans l’overlay.

## 2. Bouton

Libellé **Valider** (plus « Cranter »). Le commit HTTP ne change pas.

## 3. Contrat : pourcentages

Sur chaque ligne d’impact horaire / contrat, ajouter entre parenthèses le % du contrat :

`(pourcentage avant → pourcentage après)`

Calcul **d’affichage uniquement** : `current_hours / contracted * 100` et `trial_hours / contracted * 100` (champs déjà dans `impact.contract`). Virgule française. Si `contracted` est 0, omettre les parenthèses.

IronBee : Valider, plus de liste score, % contrat visibles sur retune / replace / swap.
