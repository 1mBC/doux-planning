# Brief — agent UI neuf (cloud) · change **bench-import** (file 71)

Le tech lead : popup **Au banc** depuis l’historique. Relis `contracts/domain/bench-import.md` UI (**gagne**). Tu ne modifies pas `contracts/`.

File 70 UI déjà sur master (Note / Voir / clic droit email). **Ne pas** casser ça. File 72 (`…`, filtre, delete) **hors scope**.

Instance **neuve**. Branche **`cursor/bench-import-ui-2843`** depuis **master**. **Ne merge pas** `master` / Python.

`/opsx-update` **`build-planning-ui`**. Reste `web/`. **`0.57.0`**, note : `Import resto vers le banc`.

Parser `/versions` : lire `origin` + `comment` si présents (défaut `catalogue` / `null` si absents — Infra peut lag).

**Process** : `npm run build` → **commit + push**. Message : `feat(web): import restaurant to bench v0.57.0`. Signal le SHA.

## Comportement

- Clic droit **nom restaurant** + bouton **Au banc** → popup preview + 4 cases ON + note /10 optionnelle + commentaire optionnel + Importer.
- POST `/v1/admin/bench/import`. Toast + lien `/admin/bench`.
- Clic droit **email** reste le lien impersonate (file 70).

## Vérif

Build. Barre **v0.57.0**. Popup cases cochées. Historique Note/Voir intacts. Banc : pas encore de `…` / filtre.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-import pushed @ <sha>, v0.57.0`
