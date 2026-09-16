# Brief — coller dans le chat **UI**

Le tech lead : la flèche vs modèle précédent est **à côté de la bulle colorée**, pas dedans. Relis **`contracts/domain/bench.md`** cellule modèle (gagne). `git pull origin master`. Branche **depuis `master`**.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Pas de HTTP. Stats banc **inchangées**.

**Process** : commit + push **ta** branche. Titre : `feat(web): bench delta arrow outside the bubble v0.44.0`. Pas de PR master. Signal le SHA.

## Comportement

- Le fond vert / bleu / rouge = **bulle** autour du **seul** chiffre ×10 vs Manuel.
- Indicateur (flèche + petit chiffre, ou liseret vert) **immédiatement à droite** de cette bulle, fond page. Pas dans la bulle.
- Clic = bulle + indicateur → le même run. Premier modèle : pas d’indicateur.
- `web/src/release.ts` + `web/package.json` → **v0.44.0**, note FR : flèche hors de la bulle delta.
- Vérifier le tableau Banc (plusieurs colonnes, deltas + / 0 / −). IronBee si dispo.

Tâches + build + vérif → **commit + push** → stop.  
Signal : `UI delta-bubble pushed @ <sha>`
