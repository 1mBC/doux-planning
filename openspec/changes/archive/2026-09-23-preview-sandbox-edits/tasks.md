## 1. Hydration

- [x] 1.1 Add a domain helper that reads `data/examples/saint-cloud.json` (or `DOUX_PLANNING_DATA`) into `Employee`, structures, hours, and `Shift` assignments without importing `doux_planning.api`, and verify a unit test round-trips Diane’s Monday midday 11:00–15:00 from the file
- [x] 1.2 Load that delivered cycle into a `PlanningStore` as published cycle + cycle sandbox via `evaluate` only, and verify hydration tests assert identical assignment tuples, `sandbox.target == "cycle"`, and that `generate_cycle` is not called
- [x] 1.3 Verify hydration does not write `data/examples/saint-cloud.json` (file bytes unchanged after the test)

## 2. Preview payload and history

- [x] 2.1 Add warning-delta identity `(severity, code, employee_id, day_index)` plus a frozen preview proposal (rank, gesture, trial result, delta, impact, scores, retune hours or replacement person or partner or fill candidate), and verify a contract_hours message change is classified unchanged while a new interdit is added
- [x] 2.2 Add `sandbox.history` plus apply-proposal (push then `apply_edit`) and undo (pop, restore assignments + `last_result`, fail on empty stack), and verify preview does not push history and two applies then one undo restores the mid state
- [x] 2.3 Verify a preview of any gesture leaves sandbox assignments and `last_result` identical to the pre-preview snapshot

## 3. Occupied gestures

- [x] 3.1 Preview retune as one timed trial (15 min, clip 0–1440, duration ≥ `min_shift_hours`), reject identity hours, and verify ±15 on Théo 11:00–16:00 returns one proposal with draft unchanged
- [x] 3.2 Preview replace by dropping the occupied shift then calling existing `rank_candidates`, excluding the holder, sort with `occupied_sort_key`, and verify Diane is absent from her occupied list while empty-slot occupancy skipping still passes
- [x] 3.3 Preview swap via `swap_shifts` against every other person’s assignment, sort with `occupied_sort_key` plus a stable partner tie-break, and verify a person’s own other shifts are omitted
- [x] 3.4 Apply one retune and one replace on a small fixture and verify sandbox assignments match the chosen trial and history has the corresponding entries

## 4. Impact, role_fit, fill

- [x] 4.1 Attach impact (new interdits, broken wishes, gesture-only contract, empty_post add/remove) plus current/trial `_attempt_key`, and verify an improved contract for A does not list unchanged B
- [x] 4.2 Clicked-slot `role_fit`: L4→L2 on post 1 is `better` 3→1, inverse `worse`, same level empty, swap uses the preview shift only
- [x] 4.3 `preview_fill` (structure span when hours omitted, occupied error, row person rank 1, others `occupied_sort_key`, empty `role_fit`) and verify empty Emma Monday midday, occupied reject, fill then undo

## 5. Guardrails

- [x] 5.1 Run engine and planning tests green without edits to FIFO, keep-best formulas, `web/`, `src/doux_planning/api/`, `contracts/`, `docs/index.html`, or the archived `define-planning-core` change
