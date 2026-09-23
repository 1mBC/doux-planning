## Why

The restaurateur must drop a staff fiche from the restaurant without touching the other team’s published cycle or live sandbox, and without deleting the platform account. Today `upsert_employee` can replace a fiche but cannot retire one, so published salle/cuisine grids and `linked_employee_ids` stay stale. After Core `remove_employee`, HTTP persist still cannot unaffiliate an account, invalidate only that employee’s sessions, or re-link the same email.

## What Changes

- Add `remove_employee(state, employee_id) -> RestaurantState` (Core, already landed).
- Unknown fiche id → existing `UnknownEmployee`.
- Drop the fiche from `state.employees` and drop that id from `identity.linked_employee_ids` (no-op if it was not linked).
- Set `published_cycles[team]` and `live_sandboxes[team]` of **that employee’s team** to `None` (sandbox drop is the same as `discard_live_sandbox`).
- Leave the **other** team’s published cycle and live sandbox untouched.
- `redeem_invite` stays unchanged so Infra can re-link the same account later.
- HTTP `DELETE /v1/staff/{id}` (Bearer company): nullify affiliated `employee_accounts` FKs together, keep email/hash, invalidate that account’s employee sessions, call Core `remove_employee`, persist fiches without `smash_live`, then clear **only** that team’s stored `published_cycles` / `live_sandboxes` keys.
- `me.restaurant_id` / `me.employee_id` nullable; unaffiliated employee login 200 with both null.
- `POST /v1/auth/link` wraps `redeem_invite` on the existing `account_id`.
- Unaffiliated `GET /v1/me/planning` → 409. PATCH omit of a still-linked fiche stays 409.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: restaurateur can retire a staff fiche; the id leaves `linked_employee_ids`.
- `cruise-planning`: retiring a fiche unpublishes and discards only that employee’s team live cycle/sandbox.
- `build-planning-api`: DELETE staff, unaffiliated `me`, `POST /v1/auth/link`, unaffiliated planning 409, nullable affiliation columns.

## Impact

- `src/doux_planning/context.py` (`remove_employee` next to `upsert_employee`). Reuse `UnknownEmployee` from `invites.py`. Call `discard_live_sandbox` for the employee’s team.
- `src/doux_planning/api/` (`app.py`, `auth.py`, `context.py`, `db.py`, `me_planning.py`, cheap `persist_maximal_result` guard) + Alembic after `20260916_0014` + TestClient tests.
- Tests in `tests/` (Core two-team mutation; HTTP delete/link/me/planning). Saint-Cloud pytest stays green.
- Do not edit `web/`, `contracts/`, `engine.py` formulas, or `redeem_invite`.
