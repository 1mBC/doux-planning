## 1. HTTP wrap

- [x] 1.1 Add `POST /v1/sandbox/enter` that hydrates Saint-Cloud only if missing, then `enter_sandbox(..., "cycle")`, and verify TestClient 200 with `target` cycle, empty history, Saint-Cloud employees, assignments+warnings, and that `data/examples/saint-cloud.json` is unchanged
- [x] 1.2 Add `GET /v1/sandbox` returning the same state, and verify 404 French when no sandbox and 200 after enter; re-enter reuses the draft
- [x] 1.3 Add `POST /v1/sandbox/preview` for retune/replace/swap wrapping the Python previews, and verify ranked `proposals` without `assignments`, no draft mutation, and French 404/400 for a missing shift
- [x] 1.4 Add `POST /v1/sandbox/commit` that replays preview and `apply_proposal` on the matching proposal, and verify a retune commit updates assignments, appends history `{index:1, gesture:retune}`, 400 French when replace lacks `employee_id`, and `GET /v1/examples/saint-cloud` still has 92 assignments
- [x] 1.5 Add `POST /v1/sandbox/undo` wrapping `undo_sandbox`, and verify one pop restores the previous draft and empty history returns 409 French

## 2. Persistence

- [x] 2.1 Persist sandbox draft, engine history, and gesture labels to Postgres when `DATABASE_URL` is set (new table, no writes to the example snapshot), and verify a restore after reset still returns the craned state; without `DATABASE_URL`, in-memory still works

## 3. Compact preview feedback

- [x] 3.1 Pass `start_minutes` and `end_minutes` into `preview_retune`, and verify TestClient retune preview returns 0 or 1 proposal, identity hours are 400 French, duration below min is 400 French, and the draft is unchanged
- [x] 3.2 Serialize proposal `impact` plus `current_score` / `trial_score` from `_attempt_key`, omit `delta` and trial-wide `warnings`, include `day_index`/`weekday` on `partner`, and verify replace/swap lists still rank by `rank`
- [x] 3.3 Add draft `score` on enter/GET/commit/undo state, and verify the keys match the contract score object
- [x] 3.4 Commit retune by re-calling `preview_retune` with the posted hours (no enumerated match), and verify history `{index:1, gesture:retune}` and `GET /v1/examples/saint-cloud` still has 92 assignments

## 4. Role fit on impact

- [x] 4.1 Serialize `impact.role_fit` from Python `RoleFitImpact` (list of 0 or 1), and verify TestClient replace has one proposal with `kind` `better` or `worse` and one with an empty list, without recomputing gaps in the adapter

## 5. Fill empty cell

- [x] 5.1 Wrap `preview_fill` / commit fill (`FillSlot`, both hours null or both ints), and verify TestClient Emma Monday midday null hours is 200 with rank 1 emma start 600 end 960 and empty `role_fit`, commit adds the shift with history `fill`, occupied preview is 409 French, and `GET /v1/examples/saint-cloud` still has 92 assignments

## 6. History recap and discard

- [x] 6.1 Store a commit recap from body + chosen proposal (`shift` or `slot`, hours, partner, impact), and verify TestClient retune GET includes the source shift and impact, undo pops it, and Postgres restore returns the same recap
- [x] 6.2 Add `POST /v1/sandbox/discard` wrapping `discard_sandbox` then `enter_sandbox(..., "cycle")`, and verify 404 French if never opened, 200 after a cran has empty history and hydrated-cycle assignments, example still 92, and Postgres deletes then rewrites the session
