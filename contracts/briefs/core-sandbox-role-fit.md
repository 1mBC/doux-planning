# Brief — coller dans le chat **Core Engine** (suite)

Le tech lead : l’overlay n’affiche plus le bloc score global. Il manque le **downrole en points** sur un replace : L4 sur un poste 1, remplacé par un L2 → on gagne 2 points. Inverse = négatif.

**Pas un nouveau change.** `/opsx-update` puis apply sur **`refine-sandbox-feedback`** (tu étends `preview_impact` / `PreviewImpact`). Pas de `preview-role-fit-impact`.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, FIFO / keep-best / `generate_cycle` / `_overqualification` / `_below_role_count`. Un seul `evaluate`. Pas d’HTTP. Pas de commit. Pas d’archive / sync. **Ne pas changer** `occupied_sort_key`.

Relis `contracts/http/v1-sandbox-edit.md` (`role_fit`) : tu le suis, tu ne le modifies pas.

## Formule

`gap = employee.level - post_level` (même terme que le moteur), **créneaux du geste seulement** :

- retune = le shift (poste inchangé → presque toujours vide) ;
- replace = le poste à pourvoir ;
- swap = les deux postes.

`current_gap` / `trial_gap` = sommes. Occupant manquant → pas de `role_fit`.  
trial < current → `{ current_gap, trial_gap, kind: "better" }` ; trial > current → `worse` ; égal → liste vide.

Pas de texte français. Pas de second scoreur.

## Tests

Poste 1, L4 → L2 : `better` 3 → 1. Inverse : `worse`. Même niveau : vide. Swap somme inchangée : vide. Draft intact.

Tâches cochées + pytest vert → stop.
