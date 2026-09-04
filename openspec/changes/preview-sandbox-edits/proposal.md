## Why

The restaurateur already receives a generated 14-day cycle, but cannot try a local edit with engine feedback before committing it. The Python sandbox can replace assignments and score them; it cannot preview a gesture, list ranked alternatives, or undo a cranted edit. That gap blocks any later overlay: the UI must not invent scoring, HTTP, or a second engine.

## What Changes

- Hydrate a `PlanningStore` from a **delivered** cycle (Saint-Cloud snapshot as the frozen seed: staff, structures, hours, assignments). `evaluate` may score that draft; `generate_cycle` MUST NOT run for hydration. The snapshot file stays read-only.
- Enter (or reuse) the **cycle** sandbox for this slice. Week-vs-cycle is not a product question here; the existing week-target sandbox stays as already specified and is unused by these gestures.
- Add **preview ≠ apply** for three gestures on an occupied slot in that sandbox:
  1. Retune start and/or end of that shift (15-minute grid, same person / day / `service_id`).
  2. Replace the person on that occupied window (remove the holder, then rank others with the existing candidate ranking).
  3. Swap that shift with another assignment (`swap_shifts`).
- Each preview proposal carries rank, the new person or hours, the engine `EngineResult` (warnings as the engine emits them), and a warning **delta** vs the current sandbox draft (added / removed / unchanged). The draft MUST NOT change on preview.
- Apply crantes one chosen proposal into the sandbox and pushes a history entry. Undo pops the last cranted state (assignments + `last_result`). No undo of a middle gesture.
- No HTTP, no React, no overlay, no auth. No second scorer. Proposal order reuses the current engine ranking (`interdit` then `souhait`, then existing tie-breaks). FIFO / keep-best generation is out of scope.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: cycle sandbox gains preview-then-apply, a stack history of cranted edits, undo of the last crant, and hydration from a delivered cycle without regeneration.
- `constraint-engine`: occupied-slot replacement ranking, retune-hours candidate enumeration + scoring, swap-partner preview lists, and warning deltas vs the current draft. Empty-slot `rank_candidates` and single-pair `swap_shifts` stay as they are.

## Impact

- Python domain only: `src/doux_planning/planning.py`, `src/doux_planning/engine.py`, possibly a small hydrate helper next to them (not under `api/`).
- Tests under `tests/` for hydrate, preview isolation, the three gestures, delta, apply, undo.
- Reads `data/examples/saint-cloud.json` for hydration tests. MUST NOT rewrite that file, `docs/index.html`, `web/`, `src/doux_planning/api/`, or `contracts/`.
- Main specs live in `openspec/specs/`. This change does not reopen or edit `openspec/changes/archive/2026-09-04-define-planning-core/`.
- HTTP overlay and persistence of sandbox history come in later Infra/UI slices after a contract freeze.
