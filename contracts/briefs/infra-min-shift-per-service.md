# Brief — agent Infra neuf (cloud) · change **min-shift-per-service**

Le tech lead : persist + HTTP **min créneau par service**. Relis `contracts/domain/min-shift-per-service.md` Infra **et** `contracts/http/v1-context.md`. **Gagnent.** Tu ne modifies pas `contracts/`.

**Attends Core** : `min_shift_for` / `Employee.min_shift_hours` mapping doivent être sur ta base (`cloud_base_branch` = branche Core). Si le mapping Core est encore un float → **stop**, remonte.

Instance **neuve**. Branche **`cursor/min-shift-per-service-infra-2843`**. **Ne merge pas** `master`. **Ne pas** réécrire Core.

`/opsx-update` **`build-planning-api`** (change `min-shift-per-service` déjà proposé par Core). Pas d’archive / sync.

**Ne pas toucher** `web/`, `engine.py` formules, `contracts/`. Reste `api/` + Alembic + TestClient.

**Process** : pytest vert → **commit + push**. Message : `feat(api): persist min shift hours per service`. Signal le SHA.

## Comportement

- GET `employees[].min_shift_hours` = **objet**, une clé par service offert, défaut 4. Plus un nombre.
- PATCH / import : objet ou nombre (compat). Clés invalides / ≤ 0 → 400.
- Alembic float → JSONB (`4` → `{}` ; autre N → les trois clés).
- Smash décocher service : drop la clé sur toutes les fiches.
- `_fiche_to_employee` / `_employee_from_json` / serialize : mapping Core, plus `float`.

## Tests

PATCH `{ evening: 3.5 }` → GET evening 3.5, midday 4 si midday offert. Nombre `4` en PATCH → objet de 4. Pytest context verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra min-shift-per-service pushed @ <sha>`
