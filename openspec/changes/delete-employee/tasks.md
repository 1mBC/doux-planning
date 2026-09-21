## 1. Core mutation

- [x] 1.1 Add `remove_employee(state, employee_id) -> RestaurantState` next to `upsert_employee` in `context.py`, and verify two teams with both published plus a salle live sandbox: removing the salle fiche drops that fiche and its id from `linked_employee_ids`, clears salle published cycle and live sandbox, and leaves cuisine published intact
- [x] 1.2 Verify an unknown fiche id raises `UnknownEmployee` and does not mutate staff, linked ids, or the other team’s published cycle; leave `redeem_invite` unchanged

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `engine.py` formulas, or `redeem_invite`
