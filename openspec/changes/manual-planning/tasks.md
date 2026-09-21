# Tasks

## 1. Seed empty team cycle

- [x] 1.1 Add `seed_empty_team_cycle(state, team) -> PublishedCycle` next to `generate_team` in `context.py` (`TeamNotReady` if not ready; same skeleton as `generate_team` with `assignments=()` and `result=evaluate(draft)`; default `search_effort`; no `generate_cycle` / `generate_for`), and verify salle ready without generate: empty assignments, `empty_post` warnings, cuisine `published_cycles` None
- [x] 1.2 Verify cuisine not ready raises `TeamNotReady` without writing either team's published cycle, and that `generate_cycle` is not called
- [x] 1.3 Verify enter + fill + apply + undo on the seeded salle cycle like `test_live_sandbox`, without calling `generate_cycle`, then `generate_team(..., minimal)` replaces the Core salle slot while cuisine stays unpublished

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `SearchEffort`, engine formulas, `stretch_to_min_shift`, keep-best, or Saint-Cloud hydrate / `state.sandbox`
