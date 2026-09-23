# Brief — coller dans le chat **UI**

Le tech lead : **banc polish** — grid aligné + hover stats interactif. Relis **`contracts/domain/bench.md`** section UI.

`git pull origin master` ; branche **depuis `master`**.

**Process** : tâches → **commit + push toi-même**. Titre : `feat(web): bench grid alignment and stats hover v0.48.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/`, `contracts/`. **Pas** de route HTTP.

## 1. Tableau banc — grid aligné

**Problème** : les deltas négatifs (juste du texte) sont moins hauts que les bulles colorées → les lignes Minimal/Optimisé/Maximal s'empilent de façon décalée entre colonnes.

**Solution** : utiliser un grid CSS pour que les 3 lignes de chaque cellule aient une **hauteur fixe identique**, quelle que soit leur contenu (bulle ou chiffre simple).

```css
.bench-cell-stack {
  display: grid;
  grid-template-rows: repeat(3, minmax(28px, auto)); /* hauteur min fixe */
  gap: 4px;
  align-items: center;
}
```

Toutes les colonnes moteur alignées horizontalement — les Mini sont sur la même ligne, les Opti sur la même ligne, etc.

## 2. Stats banc — hover interactif stylé

**Comportement** :
- Quand la souris s'approche d'un point (seuil ~20–30 px du centre), déclencher le hover
- Identifier le **modèle le plus proche** sur l'axe X
- Afficher :

### Ligne pointillée verticale
- Passe par les 3 points (min, moyenne, max) du modèle
- Style : `stroke-dasharray: 4 4`, couleur `#666`, opacity 0.7
- Du haut du graphe au bas (ou juste entre ymin et ymax)

### Labels en surimpression
- **3 notes** affichées directement sur le graphique, à côté de chaque point :
  - Min : label rouge à gauche du point
  - Moyenne : label noir/gris au-dessus du point
  - Max : label bleu à droite du point
- Format : `8.2` (1 décimale)
- Style :
  - Fond semi-transparent (`rgba(255,255,255,0.9)`)
  - Padding `2px 6px`, border-radius `4px`
  - Font bold, taille lisible (~12px)
  - Couleur texte assortie à la courbe (`#c43a3a` min, `#1c1917` moyenne, `#2f6fed` max)
  - Légère ombre ou bordure subtile pour décoller du fond

### Détection
- `onMouseMove` sur le SVG
- Calculer quel `engine_ref` est le plus proche de `mouseX`
- Si distance < seuil → afficher, sinon masquer
- Smooth : pas de clignotement

## Version

`web/src/release.ts` → `version: "0.48.0"`, `note: "Alignement banc + hover stats interactif"`.  
`web/package.json` → `"version": "0.48.0"`.

## Tests

- Tableau : les 3 lignes Mini/Opti/Max alignées entre toutes les colonnes moteur
- Stats : hover déclenche ligne + labels quand proche d'un point
- Stats : labels lisibles, pas de chevauchement avec les courbes
- Stats : hover disparaît quand souris s'éloigne
- Pas de régression sur le reste

Signal : `UI bench-polish pushed @ <sha>`
