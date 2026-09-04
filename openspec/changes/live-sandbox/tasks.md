## 1. Live sandboxes and enter / discard / publish

- [x] 1.1 Add `live_sandboxes` (salle/cuisine, default both None) plus `NoPublishedCycle` / enter / discard / publish in `context.py`, and verify cuisine without a published cycle raises without creating a draft
- [x] 1.2 Route `preview_*` / `apply_proposal` / `undo_sandbox` to `live_sandboxes[team]` when `team` is passed, and verify salle generate + enter + retune apply + undo + discard restores the published cycle while publish updates salle only

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `api/`, `contracts/`, engine formulas, hydrate Saint-Cloud, or `state.sandbox` toy behavior
