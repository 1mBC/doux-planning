## 1. Model

- [x] 1.1 Add `Wellbeing`, `{ weekday, service_id }` unavailability, and `week_label_scheme`, and verify freeze scenarios for labels, day×service blocks, and rejected legacy keys
- [x] 1.2 Align engine warnings and solver (consecutive rest per week, weekend even/odd/every_two, max services including 0, coupures including 0) and verify the freeze warning scenarios
- [x] 1.3 Map `employee_board.wishes` to `{ kind, held, … }`, adapt Saint-Cloud employees, recompute planning only if generate changes, and verify hydrate + employee_board

## 2. Guardrails

- [x] 2.1 Run domain / engine / hydrate / employee_board / generate pytest green without editing `web/`, `api/`, or `contracts/`
