# Brief — agent Core neuf (cloud) · change **min-shift-per-service**

Le tech lead : **min créneau par service**. Relis `contracts/domain/min-shift-per-service.md` section Core (gagne). Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/min-shift-per-service-core-2843`** depuis la freeze. **Ne merge pas** `master`.

Nouveau change OpenSpec **`min-shift-per-service`**. Skills → **propose puis `/opsx-apply`**. Pas d’archive / sync.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic. **Ne pas** modifier le corps de `stretch_to_min_shift`.

**Process** : pytest vert → **commit + push**. Message : `feat(core): min shift hours per service`. Signal le SHA.

## Comportement

- `Employee.min_shift_hours` = mapping sparse `morning|midday|evening` → float. Vide = 4 partout.
- `min_shift_for(employee, service_id) -> float` (défaut 4).
- Tous les `_assigned_window` + fill/retune sandbox : passer `min_shift_for(..., structure.service_id / slot.service_id)`.
- Hydrate : nombre N encore accepté (N=4 → `{}` ; sinon les services du draft à N). Pas d’édition Saint-Cloud fichier.

## Tests

Fiche evening=3, midi par défaut : stretch soir 3 h, midi 4 h. Hydrate nombre 3. Saint-Cloud verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core min-shift-per-service pushed @ <sha>`
