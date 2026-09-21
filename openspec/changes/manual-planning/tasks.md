# Tasks

## 1. Seed empty team cycle

- [x] 1.1 Add `seed_empty_team_cycle(state, team) -> PublishedCycle` next to `generate_team` in `context.py` (`TeamNotReady` if not ready; same skeleton as `generate_team` with `assignments=()` and `result=evaluate(draft)`; default `search_effort`; no `generate_cycle` / `generate_for`), and verify salle ready without generate: empty assignments, `empty_post` warnings, cuisine `published_cycles` None
- [x] 1.2 Verify cuisine not ready raises `TeamNotReady` without writing either team's published cycle, and that `generate_cycle` is not called
- [x] 1.3 Verify enter + fill + apply + undo on the seeded salle cycle like `test_live_sandbox`, without calling `generate_cycle`, then `generate_team(..., minimal)` replaces the Core salle slot while cuisine stays unpublished

## 2. Guardrails

- [x] 2.1 Run `pytest` green without edits to `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `SearchEffort`, engine formulas, `stretch_to_min_shift`, keep-best, or Saint-Cloud hydrate / `state.sandbox`

## 3. HTTP API (`build-planning-api`)

- [x] 3.1 Always emit JSONB `published_cycles` with four keys (`minimal|optimized|maximal|manuel`); coerce a 3-key blob to `manuel: null` and an old flat cycle to `versions.optimized` + `manuel: null`; `latest` newest `generated_at` with tie-break manuel > maximal > optimized > minimal; keep generate/bench `EFFORTS` as the three computes
- [x] 3.2 `POST /v1/generate` with `search_effort: "manuel"` → 400 `Champs invalides.`; generate never writes `versions.manuel`; a later generate may take `latest` and must leave the manuel slot intact
- [x] 3.3 `POST /v1/live/sandbox/{team}/enter` `search_effort=manuel`: not ready → 409 `Cette équipe n'est pas prête à calculer.`; slot null → Core `seed_empty_team_cycle` then enter, persist live only; slot exists → hydrate then enter. Discard never-published manuel → re-seed empty, empty history. Publish manuel → `versions.manuel` with `search_effort: "manuel"`, `generated_at` now, no duration/engine_ref, no `generate_logs` row, recompute `latest`, close draft. Preview/commit/undo wrap Core and do not rescore
- [x] 3.4 TestClient coverage (`skipif` without `DATABASE_URL`): enter manuel without generate → empty assignments + facts; fill/commit; publish → GET `versions.manuel` + `latest` manuel and generate_logs count unchanged; generate optimized after → manuel intact; POST generate manuel → 400; 3-key cycles coerce; existing live/generate tests green
