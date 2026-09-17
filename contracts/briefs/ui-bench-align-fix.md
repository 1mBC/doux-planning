# Brief — coller dans le chat **UI**

Le tech lead : **banc alignement fix**. Les lignes Mini/Opti/Max doivent être alignées horizontalement à travers toutes les colonnes.

`git pull origin master` ; branche **depuis `master`**.

**Process** : tâches → **commit + push toi-même**. Titre : `fix(web): bench row alignment fixed height v0.48.1`. Pas de PR master. Signal le SHA.

## Problème

Actuellement chaque colonne a son propre grid `.bench-engine-stack` avec `grid-template-rows: repeat(3, minmax(28px, auto))`. Le `auto` fait que si une cellule a une bulle (plus haute) et une autre a juste du texte (moins haut), les hauteurs divergent → décalage horizontal entre colonnes.

## Solution

Forcer une **hauteur fixe** (pas min-height) sur chaque ligne :

```css
.bench-engine-stack {
  display: grid;
  grid-template-rows: repeat(3, 28px); /* hauteur FIXE, pas minmax */
  gap: 4px;
  align-items: center;
}
```

Ou si 28px est trop serré pour les bulles, augmenter à 32px. L'important c'est que ce soit **fixe** partout.

Vérifier aussi que `.bench-engine-line` a une hauteur contrainte :

```css
.bench-engine-line {
  height: 28px; /* ou 32px — même valeur que le grid */
  /* ... */
}
```

## Version

`web/src/release.ts` → `version: "0.48.1"`, `note: "Alignement lignes banc corrigé"`.  
`web/package.json` → `"version": "0.48.1"`.

## Test

- Ouvrir `/admin/bench`
- Vérifier que toutes les lignes Minimal sont à la même hauteur horizontale
- Idem pour Optimisé et Maximal
- Pas de décalage entre une colonne avec bulles colorées et une avec chiffres rouges

Signal : `UI bench-align-fix pushed @ <sha>`
