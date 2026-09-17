# Brief — coller dans le chat **UI**

Le tech lead : **banc — meilleur par ligne**. Affichage des scores dans le tableau banc : on met en avant le meilleur moteur de chaque ligne. Relis **`contracts/domain/bench.md`** section UI (lignes ~330).

`git pull origin master` ; branche **depuis `master`**.

**Process** : tâches → **commit + push toi-même**. Titre : `feat(web): bench table best engine per row v0.47.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/`, `contracts/`. **Pas** de route HTTP. Pas de Core / Infra.

## Comportement

**Avant** : chaque cellule modèle affiche delta vs Manuel (bulle fond coloré) + flèche vs modèle précédent.

**Après** :
- **Ligne** = (dataset, effort). Pour chaque ligne, identifier le(s) **meilleur(s)** moteur(s) = note `global` la plus haute.
- **Meilleur(s)** : delta vs Manuel (×10 entière), **bulle avec fond coloré** comme avant. Si **égalité** → tous les ex-aequo ont la bulle.
- **Autres** : écart vs le meilleur de la ligne (×10 entière, ex: `-1`, `-2`, `-3`). **Pas de fond**, **pas de flèche**. Couleur du texte **crescendo rouge** (plus l'écart est grand, plus rouge). Pas de bulle, juste le chiffre.
- Tiret si pas de run.
- Clic → `/admin/bench/run/{run_id}` (bulle ou chiffre).

## Logique

```typescript
// Pour chaque ligne (dataset, effort)
const rowCells = engineRefs.map(ref => dataset.by_ref[ref]?.[effort]);
const bestGlobal = Math.max(...rowCells.filter(c => c?.global != null).map(c => c.global));

rowCells.forEach((cell, i) => {
  if (cell?.global == null) return; // tiret
  const isBest = cell.global === bestGlobal;
  if (isBest) {
    // bulle avec fond coloré, delta vs Manuel
    const delta = round((cell.global - manual.global) * 10);
  } else {
    // chiffre sans fond, écart vs meilleur
    const gap = round((cell.global - bestGlobal) * 10); // toujours négatif ou 0
  }
});
```

## Chrome

- **Bulle meilleur** : `.bench-cell` existant (padding `6px 8px`, bordure `#ddd` radius 6, `font-weight` 650, fond coloré crescendo).
- **Autres** : juste le chiffre (ex: `-2`), pas de bordure, pas de fond. Couleur texte crescendo rouge : `hsl(0, 70%, lerp(50%, 30%, |gap|/10))` ou similaire. Clamp à 1 point d'écart.
- Plus de flèche nulle part.

## Version

`web/src/release.ts` → `version: "0.47.0"`, `note: "Meilleur moteur mis en avant sur le banc"`.  
`web/package.json` → `"version": "0.47.0"`.

## Tests

- Ligne avec un seul meilleur → bulle sur lui, chiffres écart sur les autres.
- Ligne avec égalité → bulles sur tous les ex-aequo.
- Ligne sans run → tirets partout.
- Écart `-3` plus rouge que `-1`.
- Clic fonctionne sur bulle et sur chiffre.

Signal : `UI bench-best-line pushed @ <sha>`
