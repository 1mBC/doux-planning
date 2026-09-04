## Why

The restaurateur overlay is already wired to Python preview, but the feedback is unreadable: retune dumps hundreds of hour combinations, replace/swap rank by **cycle totals** (so 1 interdit + 1 souhait cassé can beat 1 interdit), and the delta lists unchanged cycle noise. Scoring and ranking must be fixed in the engine module, not in the UI.

## What Changes

- Retune preview becomes **one trial**: caller passes `start_minutes` and `end_minutes` (15-minute quantum, duration ≥ `min_shift_hours`, clip 0–1440). Same hours as the current shift → error, not a fake success. No ±2 h enumeration.
- Occupied **replace** and **swap** lists are sorted by **delta vs the current draft**: added interdits, then added souhaits, then hours-miss change (`_hours_miss` trial vs current), then keep-best `_attempt_key` of the trial. Empty-slot `rank_candidates` is unchanged.
- Each proposal carries a **local impact** (new interdits, broken wishes, contract closer/farther/excess for people in the gesture only, `empty_post` added or removed, **role_fit** downrole points on the **clicked slot only**) plus the keep-best key for current draft and trial. Overlay must not need `delta.unchanged` or the full cycle added list.
- Empty-cell **fill**: `preview_fill` adds one trial shift per eligible candidate; row person ranks first when they can hold the post; others use `occupied_sort_key`. Same hours for every candidate. `role_fit` is empty (no current occupant). `apply_proposal` / undo stay.

`preview-sandbox-edits` artifacts stay frozen; this change supersedes retune enumeration and total-based occupied ranking in code.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `constraint-engine`: single-step retune trial; occupied replace/swap rank by warning delta and hours-miss change; preview impact summary including clicked-slot `role_fit`; empty-cell `preview_fill`; expose keep-best `_attempt_key` as the planning score.
- `cruise-planning`: sandbox preview still does not mutate the draft; proposals carry impact (including `role_fit` / fill) + before/after score instead of relying on unchanged-warning dumps.

## Impact

- `src/doux_planning/planning.py` (preview APIs). May import existing `_attempt_key` / `_hours_miss` from `engine.py` without changing those formulas or `generate_cycle`.
- Tests in `tests/test_preview_sandbox.py` (and new cases). Do not edit `preview-sandbox-edits/` artifacts, `api/`, `web/`, `contracts/`, Pages, or the V0 archive.
- HTTP adapter still calls `preview_retune(shift)` without times; Infra updates after this Python freeze. Core does not patch `api/`.
