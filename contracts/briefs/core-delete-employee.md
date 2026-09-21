# Brief — agent Core neuf (cloud) · change **delete-employee**

Le tech lead : **remove_employee**. Relis `contracts/domain/delete-employee.md` section Core (gagne). Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/delete-employee-core-2843`** depuis la base freeze. **Ne merge pas** `master`.

Nouveau change OpenSpec **`delete-employee`**. Skills → **propose puis `/opsx-apply`**. Pas d’archive / sync. Pas de `/opsx-update` sandbox / generate.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `engine.py` formules. Pas d’HTTP. Pas de comptes / sessions / email.

**Process** : pytest vert → **commit + push ta branche**. Message : `feat(core): remove_employee unpublish own team`. Signal le SHA.

## Comportement

- `remove_employee(state, employee_id) -> RestaurantState`. Absent → `UnknownEmployee` (existant).
- Retire la fiche + l’id de `linked_employee_ids`.
- `published_cycles[team]` et `live_sandboxes[team]` de **son** équipe → `None`. **L’autre équipe intacte.**
- `redeem_invite` inchangé (Infra s’en sert pour le re-lien).

## Tests

Deux équipes avec publié + sandbox live salle → remove salle : salle vide, cuisine publié intact, linked sans l’id. Id inconnu → `UnknownEmployee`. Saint-Cloud verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core delete-employee pushed @ <sha>`
