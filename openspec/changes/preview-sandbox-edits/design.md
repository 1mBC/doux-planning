## Context

See proposal.md for why. Main engine contract is already in `openspec/specs/` (archived V0). `PlanningStore` already has `enter_sandbox`, `apply_edit`, `generate_into_sandbox`. `rank_candidates` skips anyone overlapping the window (including the holder of an occupied slot). `swap_shifts` scores one pair. `Warning.key()` includes the message and is used for publish acknowledgement — leave that key alone.

This slice adds preview, history, undo, hydration, and three gesture enumerations on the **cycle** sandbox. No HTTP.

## Goals / Non-Goals

**Goals:**
- Python APIs a later overlay can call: hydrate delivered cycle, preview three gestures, apply one proposal, undo last crant.
- One warning delta helper shared by all previews.
- Tests that prove preview isolation and Saint-Cloud hydration without rewriting the snapshot.

**Non-Goals:**
- Changing FIFO pairing, keep-best `_attempt_key`, empty-slot `rank_candidates`, or single-pair `swap_shifts` semantics.
- Week sandbox UX, publish/discard, HTTP shapes, React, `contracts/`, `api/`, GitHub Pages HTML.
- Persisting history across process restart (in-memory stack on `Sandbox` is enough).

## Decisions

### 1. Hydration lives in the domain package, not `api/`

Read `data/examples/saint-cloud.json` from a helper next to `planning.py` (same data-dir rule as the files on disk: repo `data/` or `DOUX_PLANNING_DATA`). Map JSON → `Employee` / `ServiceStructure` / `RestaurantHours` / `Shift`, `add_restaurant`, set `PublishedCycle` with those assignments, `evaluate` for `result`, then `enter_sandbox(..., "cycle")`. Never import `doux_planning.api`. Never call `generate_cycle`. If a sandbox is already open, discard it first so hydration always yields a clean cycle sandbox of the delivered draft.

Alternative: call `api.examples.load_example_file`. Rejected: this slice must not depend on the HTTP/adapter layer.

### 2. Shared `PreviewProposal` + apply/undo on the store

A frozen proposal holds: `rank`, gesture kind (`retune` | `replace` | `swap`), the trial `EngineResult`, warning delta, and the fields the overlay needs (new start/end, or replacement employee, or partner shift). Preview functions clone the draft, score trials, return a list; they must not assign `state.sandbox`. Apply copies current `(assignments, last_result)` onto `sandbox.history`, then reuses `apply_edit` with the proposal’s trial assignments (rescore, do not trust a stale result). Undo pops history and writes those assignments/`last_result` back. Empty history raises; draft unchanged.

Alternative: mutate the sandbox during preview and “roll back”. Rejected: easy to leak a trial if a caller aborts.

Alternative: undo any crant in the middle of the stack. Rejected: later crants would need replay/rebase. Stack undo only (last in, first out).

### 3. Warning delta ignores message text

Identity for added/removed/unchanged is `(severity, code, employee_id, day_index)`. Do not change `Warning.key()` (publish still needs the message). A `contract_hours` warning that only changes the hour count in the text is **unchanged**. Messages shown on the proposal are `result.warnings` as emitted.

Alternative: use `Warning.key()` including message. Rejected: every retune would look like remove+add for the same contract miss.

### 4. Retune enumerates start × end in the ±2 h band

15-minute quantum. Start in `[current_start - 120, current_start + 120]`, end in `[current_end - 120, current_end + 120]`, clip to `[0, 1440]`, keep `start < end`, duration ≥ that employee’s `min_shift_hours`, drop the identity pair. Same person, day, `service_id`, team, `post_level`. Score each trial with `evaluate`. Sort like `Candidate` without inventing a new key: `(interdit_count, souhait_count, start_minutes, end_minutes)`. Do not clip to the structure span: out-of-wave times are valid trials and surface as couverture via `evaluate`.

Alternative: restaurateur types one start/end and we only score that trial. Set aside: retune, replace, and swap then share the same overlay (ranked options, impact per option). We try that first.

Alternative: slide a fixed duration only. Rejected: début and/or fin move independently.

### 5. Occupied replace is “drop holder, then existing rank”

`with_assignments` minus that one shift, then `rank_candidates` on the same window, then drop the incumbent if they reappear (they are no longer occupying that window). Do not change `rank_candidates` occupancy rules for empty slots.

Alternative: a flag on `rank_candidates` to ignore the holder. Rejected: extra branch on the empty-slot path.

### 6. Swap preview is `swap_shifts` against every other person’s assignment

Partners = other assignments whose `employee_id` differs. Same person’s other shifts are omitted. Sort `(interdit_count, souhait_count, partner.day_index, partner.service_id, partner.employee_id, partner.start_minutes)`. Apply is that pair’s `swap_shifts` assignments, not a new swap implementation.

Alternative: same-day or same-service partners only. Rejected: the brief is “échanger ce créneau avec un autre shift”; ranking already sinks illegal swaps.

### 7. Cycle target only for this slice; do not reverse week sandbox

`enter_sandbox` still accepts `week`. Hydration and the three gestures always use `target="cycle"`. Do not add a product prompt and do not delete week support.

## Risks / Trade-offs

- [Retune × Saint-Cloud can mean ~200 `evaluate` calls] → Mitigation: correctness tests use a tiny draft; one Saint-Cloud test hydrates and previews a single known shift without asserting the full candidate count.
- [Swap preview is O(n) evaluates on 92 shifts] → Acceptable for an in-memory cycle; do not add a second scorer to trim the list.
- [Generic `apply_edit` from older tests does not push history] → Gesture apply always pushes; leave `apply_edit` as the primitive. Undo is defined for crants made through apply-proposal.

## Migration Plan

None. New in-memory APIs. No schema, no HTTP.

## Open Questions

None that change the specs. Overlay field names wait for a later contract; this slice only needs enough Python data for rank, person or hours, warnings, and delta.
