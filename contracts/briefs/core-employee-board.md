# Brief — coller dans le chat **Core Engine**

Le tech lead : grille employé. Premier maillon **Python** : `employee_board` sur le cycle **publié** de l’équipe (grille complète + contrat/souhaits lecture). Relis `contracts/domain/employee-board.md` (tu le suis, tu ne le modifies pas).

`git fetch origin master` ; master doit contenir live mergé (`live_sandboxes`, `publish_live_sandbox`, `generate_team`). Si `generate_team` / `live_sandboxes` manquent → **stop**, remonte au facteur. Branche **`employee/core` depuis `master`**. Pas `live/core`.

Nouveau change OpenSpec **`employee-board`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox joujou / live-sandbox / generate. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `engine.py` formules, preview/fill, hydrate. Pas d’HTTP. `employee_view` existant inchangé.

## Comportement

- `employee_board(state, employee_id)` selon le freeze. Assignments = **équipe entière** publiée. Jamais le brouillon live. Souhaits = prefs fiche + codes warning du result publié (mapping du freeze). Pas de `generate_cycle`.

## Tests

Salle generate minimal + souhait sur A → grille salle complète ; cran live non publié invisible ; cuisine sans cycle → assignments vides ; id inconnu → `UnknownEmployee`. Pytest existants verts.

Tâches cochées + pytest vert → stop.
