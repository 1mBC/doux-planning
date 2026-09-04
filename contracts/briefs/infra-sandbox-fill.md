# Brief — coller dans le chat **Infra** (suite)

Le tech lead : Core a `preview_fill` + `OccupiedSlotError` + `FillSlot`. Swap `role_fit` est déjà du JSON (rien à changer là). Contrat : `contracts/http/v1-sandbox-edit.md` (relis, ne modifie pas).

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-api`**. Pas d’auth/jobs.

**Ne pas** éditer `planning.py` / `engine.py` / `hydrate.py` / `web/`. Si `preview_fill` n’existe pas : stop.

## Preview / commit `fill`

- `gesture: "fill"` n’utilise **pas** `parse_shift`. Body : `slot` `{ employee_id, day_index, weekday, service_id, team }` + `start_minutes` / `end_minutes` (nombres **ou** `null`). Les deux null → `preview_fill(..., None, None)` (span structure). Un seul des deux → 400. Les deux nombres → les passer.
- Sérialiser les propositions comme les autres (`gesture` `"fill"`, `start_minutes` / `end_minutes` / `employee_id`, `impact`, scores).
- `OccupiedSlotError` **avant** le `ValueError` générique → **409** français (case déjà occupée). Service fermé / durée min / grille → 400 français déjà branchés si le message contient `min_shift_hours` / `15-minute grid` ; ajouter un 400 français pour service fermé.
- Commit : `slot` + `employee_id` + start/end ; rejouer `preview_fill` ; matcher `employee_id` ; `apply_proposal`. History `{ gesture: "fill" }`.
- TestClient : Emma lundi midi, heures null → 200, rang 1 `emma`, start 600 / end 960, `role_fit` `[]` ; commit pose le shift ; GET exemple toujours 92. Occupé → 409. Dual-read. Pas d’archive / commit.

`tests/test_preview_sandbox.py` : cas HTTP seulement, ne pas réécrire les tests Python Core.
