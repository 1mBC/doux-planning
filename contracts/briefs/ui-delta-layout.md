# Brief — coller dans le chat **UI**

Le tech lead : **rapide**. Relis **`contracts/domain/bench.md`** cellule modèle (gagne). `git pull origin master`. Branche **depuis `master`**.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Stats **inchangées**.

**Process** : commit + push. Titre : `feat(web): restore bench delta bubble size, drop zero bar v0.45.0`. Pas de PR master. Signal le SHA.

## Comportement

- **Plus** de liseret vert si delta vs modèle précédent = 0 → **rien**.
- **Plus** de contour commun autour de (chiffre + flèche). La wrap n’a ni bordure ni fond.
- La **bulle** du chiffre ×10 vs Manuel = **même taille / padding / bordure / graisse** que `.bench-cell` **avant** d’y coller la flèche (`6px 8px`, radius 6, bordure `#ddd`). La flèche à droite **ne réduit pas** ce chiffre.
- Flèche + petit chiffre : **tels quels** (bleu / rouge, crescendo).
- `release.ts` + `package.json` → **v0.45.0**, note FR : bulle delta comme avant, plus de trait vert à zéro.
- Vérifier le tableau Banc. IronBee si dispo.

Commit + push → stop.  
Signal : `UI delta-layout pushed @ <sha>`
