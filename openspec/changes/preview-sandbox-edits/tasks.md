## 1. Hydration

- [x] 1.1 Add a domain helper that reads `data/examples/saint-cloud.json` (or `DOUX_PLANNING_DATA`) into `Employee`, structures, hours, and `Shift` assignments without importing `doux_planning.api`, and verify a unit test round-trips Diane’s Monday midday 11:00–15:00 from the file
- [x] 1.2 Load that delivered cycle into a `PlanningStore` as published cycle + cycle sandbox via `evaluate` only, and verify hydration tests assert identical assignment tuples, `sandbox.target == "cycle"`, and that `generate_cycle` is not called
- [x] 1.3 Verify hydration does not write `data/examples/saint-cloud.json` (file bytes unchanged after the test)

## 2. Preview payload and history

- [x] 2.1 Add warning-delta identity `(severity, code, employee_id, day_index)` plus a frozen preview proposal (rank, gesture, trial result, delta, retune hours or replacement person or partner shift), and verify a contract_hours message change is classified unchanged while a new interdit is added
- [x] 2.2 Add `sandbox.history` plus apply-proposal (push then `apply_edit`) and undo (pop, restore assignments + `last_result`, fail on empty stack), and verify preview does not push history and two applies then one undo restores the mid state
- [x] 2.3 Verify a preview of any gesture leaves sandbox assignments and `last_result` identical to the pre-preview snapshot

## 3. Gestures

- [x] 3.1 Enumerate retune candidates (±2 h start and end, 15 min, clip 0–1440, duration ≥ `min_shift_hours`, drop identity pair), score each with `evaluate`, sort `(interdit, souhait, start, end)`, and verify Théo 11:00–16:00 proposals stay Monday midday Théo and omit sub-minimum durations
- [x] 3.2 Preview replace by dropping the occupied shift then calling existing `rank_candidates`, excluding the holder, and verify Diane is absent from her occupied Monday midday list while empty-slot occupancy skipping still passes the existing ranking test
- [x] 3.3 Preview swap by calling existing `swap_shifts` against every other person’s assignment, sort with the same interdit-then-souhait key plus a stable partner tie-break, and verify a person’s own other shifts are omitted and apply matches `swap_shifts` on that pair
- [x] 3.4 Apply one retune and one replace proposal on a small fixture and verify sandbox assignments match the chosen trial and history has the corresponding entries

## 4. Guardrails

- [x] 4.1 Run the existing engine and planning tests and verify they still pass with no edits to FIFO, keep-best, `web/`, `src/doux_planning/api/`, `contracts/`, `docs/index.html`, or the archived `define-planning-core` change
