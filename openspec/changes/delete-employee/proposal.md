## Why

The restaurateur must drop a staff fiche from the restaurant without touching the other team’s published cycle or live sandbox, and without deleting the platform account. Today `upsert_employee` can replace a fiche but cannot retire one, so published salle/cuisine grids and `linked_employee_ids` stay stale.

## What Changes

- Add `remove_employee(state, employee_id) -> RestaurantState`.
- Unknown fiche id → existing `UnknownEmployee`.
- Drop the fiche from `state.employees` and drop that id from `identity.linked_employee_ids` (no-op if it was not linked).
- Set `published_cycles[team]` and `live_sandboxes[team]` of **that employee’s team** to `None` (sandbox drop is the same as `discard_live_sandbox`).
- Leave the **other** team’s published cycle and live sandbox untouched.
- `redeem_invite` stays unchanged so Infra can re-link the same account later.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: restaurateur can retire a staff fiche; the id leaves `linked_employee_ids`.
- `cruise-planning`: retiring a fiche unpublishes and discards only that employee’s team live cycle/sandbox.

## Impact

- `src/doux_planning/context.py` (`remove_employee` next to `upsert_employee`). Reuse `UnknownEmployee` from `invites.py`. Call `discard_live_sandbox` for the employee’s team.
- Tests in `tests/` (two teams, published both, live sandbox on salle, unknown id). Saint-Cloud pytest stays green.
- Do not edit `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `engine.py` formulas, or `redeem_invite`.
