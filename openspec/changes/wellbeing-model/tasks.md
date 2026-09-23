## 1. Model

- [x] 1.1 Add `Wellbeing`, `{ weekday, service_id }` unavailability, and `week_label_scheme`, and verify freeze scenarios for labels, day×service blocks, and rejected legacy keys
- [x] 1.2 Align engine warnings and solver (consecutive rest per week, weekend even/odd/every_two, max services including 0, coupures including 0) and verify the freeze warning scenarios
- [x] 1.3 Map `employee_board.wishes` to `{ kind, held, … }`, adapt Saint-Cloud employees, recompute planning only if generate changes, and verify hydrate + employee_board
- [x] 1.4 Make posed `max_services` a hard fill skip (same week counter as evaluate), set `engine_ref` `core-1`, and verify Marais Elsa has no evening shift
- [x] 1.5 Fill scarce windows first (`fewest`), set `engine_ref` `core-2`, and verify Atelier Saturday evening empties drop below 4 without regressing Marais Elsa
- [x] 1.6 Pipe seeders → SAT locks → fill (`core-3`): T=3, five seeders, copies 10/50, infeasible seed discarded, `VERSION` `core-3`
- [x] 1.7 Fill anti-coupure: drop `int(not started_day)`, penalize creating a gap, locks frozen, fewest-first unchanged

## 2. Guardrails

- [x] 2.1 Run domain / engine / hydrate / employee_board / generate pytest green without editing `web/`, `api/`, or `contracts/`
- [x] 2.2 Verify `engine_ref() == "core-3"`, minimal 0 lock / 16 max, lock not moved, infeasible seed ignored, `run_bench(tight, halles, minimal)` green, 50 listings, engine pytest green
