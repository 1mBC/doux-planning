## 1. Core mutation

- [x] 1.1 Add `remove_employee(state, employee_id) -> RestaurantState` next to `upsert_employee` in `context.py`, and verify two teams with both published plus a salle live sandbox: removing the salle fiche drops that fiche and its id from `linked_employee_ids`, clears salle published cycle and live sandbox, and leaves cuisine published intact
- [x] 1.2 Verify an unknown fiche id raises `UnknownEmployee` and does not mutate staff, linked ids, or the other team’s published cycle; leave `redeem_invite` unchanged

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `engine.py` formulas, or `redeem_invite`

## 3. HTTP API (`build-planning-api`)

- [x] 3.1 Alembic after `20260916_0014`: make `employee_accounts.restaurant_id` and `employee_id` nullable with CHECK both-null or both-non-null; make `sessions.restaurant_id` nullable; update `EmployeeAccountRow` and `AuthSession`; do not drop `account_emails` uniqueness
- [x] 3.2 Implement `DELETE /v1/staff/{id}` (Bearer company, 200 Context): unknown/other restaurant 404 `Fiche introuvable.`; employee Bearer 403; nullify affiliated account FKs together, keep email/hash, invalidate that account’s employee sessions; `remove_employee` then `_persist_state` without `smash_live`; set only that team’s stored `published_cycles` / `live_sandboxes` keys to `None`. PATCH omit of a still-linked fiche stays 409
- [x] 3.3 Allow nullable `restaurant_id` / `employee_id` on `_me_payload`, `_issue_session`, login, and `GET /v1/me`. Unaffiliated employee login 200 with both null. `require_employee_session` still requires affiliation for affiliated routes
- [x] 3.4 Implement `POST /v1/auth/link` `{ company_code, employee_id }` wrapping `redeem_invite` with the existing `account_id` and writing affiliation on the same row. Map unknown fiche to 404 `Fiche introuvable.` (leave register mapping unchanged). Wire the route in `app.py`. No `employee_token`
- [x] 3.5 `GET /v1/me/planning` when `employee_id` or `restaurant_id` is null → 409 `Vous n'êtes rattaché à aucun restaurant.` Do not call `employee_board`
- [x] 3.6 Cheap persist guard in `persist_maximal_result`: if any assignment `employee_id` is no longer a fiche of that restaurant, fail the job with a French detail and do not write `published_cycles`. No cancel route
- [x] 3.7 TestClient coverage (`skipif` without `DATABASE_URL`): linked DELETE 200 + context without the fiche + login both ids null + planning 409 + link to another unlinked fiche 200; account+email kept and old Bearer 401; PATCH omit linked 409; cuisine published and live intact when deleting a salle employee; employee 403; unknown id 404; link error table; existing auth / context / me_planning / generate green
