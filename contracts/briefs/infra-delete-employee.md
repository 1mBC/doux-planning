# Brief — agent Infra neuf (cloud) · change **delete-employee**

Le tech lead : HTTP + persist **delete salarié** (compte conservé). Relis `contracts/domain/delete-employee.md` **et** les deltas `contracts/http/v1-auth.md`, `v1-context.md`, `v1-me-planning.md`. **Gagnent.** Tu ne modifies pas `contracts/`.

**Attends Core** : `git fetch` ; `remove_employee` doit être sur ta base (branche Core mergée dans la base freeze, ou `cursor/delete-employee-core-2843` si le facteur l’a mise en `cloud_base_branch`). Si `remove_employee` manque → **stop**, remonte.

Instance **neuve**. Branche **`cursor/delete-employee-infra-2843`**. **Ne merge pas** `master`. **Ne pas** réécrire Core.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync.

**Ne pas toucher** `web/`, `engine.py`, `contracts/`. Reste `api/` + Alembic + TestClient.

**Process** : pytest vert → **commit + push**. Message : `feat(api): delete staff keep employee account`. Signal le SHA.

## Comportement

- `DELETE /v1/staff/{id}` Bearer company → Core `remove_employee` + persist. Compte : **nullifier** `restaurant_id`+`employee_id`, **garder** email/hash, **invalider** ses sessions. FK avant delete fiche.
- PATCH employees omit liée → **toujours** 409.
- `me.restaurant_id` nullable. Employee sans affiliation : login 200, les deux ids `null`.
- `POST /v1/auth/link` `{ company_code, employee_id }` Bearer employee non affilié → `redeem_invite` + même ligne compte. Détails FR du freeze.
- `GET /v1/me/planning` sans affiliation → 409 `Vous n'êtes rattaché à aucun restaurant.`
- Jobs : **pas** de route cancel. Garde-fou persist worker si cheap (assignment vers fiche disparue → job failed, pas d’écriture). Sinon skip, dis-le.

## Tests

Fiche liée : DELETE 200, GET context sans la fiche, login employé 200 `employee_id` null, planning 409, link vers une **autre** fiche OK. PATCH omit liée 409. Cuisine publié intact si delete salle. Employee 403 sur DELETE. Pytest existants verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra delete-employee pushed @ <sha>`
