## Why

The restaurateur already receives a generated 14-day cycle, but cannot try a local edit with engine feedback before committing it. Preview, ranked alternatives, local impact, empty-cell fill, and undo must live in Python so the overlay never invents scoring.

`refine-sandbox-feedback` was an incremental overlay-feedback change that should have been an update of this change. It is folded here.

## What Changes

- Hydrate a `PlanningStore` from a **delivered** cycle (Saint-Cloud snapshot). `evaluate` may score that draft; `generate_cycle` MUST NOT run. The snapshot file stays read-only. Cycle sandbox only.
- **Preview ≠ apply** for occupied slots: retune (one timed trial), replace, swap; and **fill** for an empty row cell.
- Retune: caller passes `start_minutes` and `end_minutes` (15-minute grid, duration ≥ `min_shift_hours`, clip 0–1440). Identity hours → error. No ±2 h enumeration.
- Occupied replace/swap rank by **delta vs current draft**: added interdits, added souhaits, hours-miss change, then `_attempt_key`. Empty-slot `rank_candidates` unchanged.
- Each proposal carries **impact** (new interdits, broken wishes, gesture-only contract, `empty_post` add/remove, clicked-slot `role_fit`) plus keep-best current/trial scores. Overlay must not need `delta.unchanged`.
- Fill: `preview_fill` with structure-span default hours; row person rank 1 when eligible; others `occupied_sort_key`. Occupied row cell → error.
- Apply crantes one proposal; undo pops the last crant. No HTTP, no React, no second scorer.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: cycle sandbox preview-then-apply, history, undo, hydration without regeneration; proposals carry impact + scores; fill preview does not mutate the draft.
- `constraint-engine`: single-step retune; occupied rank by warning delta; impact including clicked-slot `role_fit`; `preview_fill`; keep-best `_attempt_key` on proposals. Empty-slot `rank_candidates` and `swap_shifts` stay.

## Impact

- Python domain: `src/doux_planning/planning.py`, `src/doux_planning/hydrate.py`. May import `_attempt_key` / `_hours_miss` from `engine.py` without changing those formulas.
- Tests in `tests/test_preview_sandbox.py`. MUST NOT rewrite `data/examples/saint-cloud.json`, `web/`, `api/`, or `contracts/`.
- HTTP overlay and persistence are Infra/UI (`sandbox-edit-api`, `sandbox-edit-ui`).
