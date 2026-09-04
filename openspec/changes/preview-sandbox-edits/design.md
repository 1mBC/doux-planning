## Context

See proposal.md. `PlanningStore` already has `enter_sandbox`, `apply_edit`. `rank_candidates` skips overlapping occupants. `swap_shifts` scores one pair. `_attempt_key` / `_hours_miss` stay in `engine.py`. This change is the **Python sandbox** as shipped (hydrate, preview, impact, fill, apply, undo). HTTP is out of scope.

`refine-sandbox-feedback` is folded: one-shot retune, delta ranking, impact, `role_fit`, `preview_fill`.

## Goals / Non-Goals

**Goals:**
- Hydrate delivered cycle; preview retune/replace/swap/fill; apply; undo last crant.
- Compact `PreviewImpact` + keep-best scores on each proposal.

**Non-Goals:**
- FIFO / keep-best formulas, empty-slot `rank_candidates` semantics, `generate_cycle`.
- HTTP, React, `contracts/`, publish, auth, week sandbox UX.

## Decisions

### 1. Hydration lives in the domain package

Read `data/examples/saint-cloud.json` from `hydrate.py`. Map JSON → domain, `PublishedCycle`, `evaluate`, `enter_sandbox(..., "cycle")`. Never import `doux_planning.api`. Never call `generate_cycle`.

### 2. Shared `PreviewProposal` + apply/undo

Frozen proposal: rank, gesture, trial `EngineResult`, warning delta, **impact**, current/trial `_attempt_key`, hours / replacement / partner / fill candidate. Preview does not assign `state.sandbox`. Apply pushes history then `apply_edit`. Undo pops. Empty history raises.

### 3. Warning delta ignores message text

Identity `(severity, code, employee_id, day_index)`. Overlay display uses **impact**, not `delta.unchanged`.

### 4. Retune is one timed trial

`preview_retune(id, shift, start, end)` → 0 or 1 proposal. Grid 15, clip 0–1440, duration ≥ min. Identity → `IdentityRetuneError`. No ±2 h enumeration.

### 5. Occupied replace/swap: build trials then re-sort by delta

Drop holder then `rank_candidates`; swap via `swap_shifts`. Sort `occupied_sort_key`: added interdit, added souhait, hours-miss delta, `_attempt_key`.

### 6. Impact is filtered delta + contract + clicked-slot `role_fit`

See folded refine design: `new_interdits`, `broken_wishes` (no `contract_hours`), contract closer/farther/excess for gesture people, `empty_post` add/remove, `role_fit` on the **clicked** shift only.

### 7. Fill is `preview_fill`

Structure span when hours omitted. `post_level` = row `role.level`. `OccupiedSlotError` if the cell is already filled. Rank 1 = row person when eligible.

### 8. Cycle target only; do not reverse week sandbox

Gestures use `target="cycle"`. `enter_sandbox` still accepts `week`.

## Risks / Trade-offs

- [Swap preview is O(n) evaluates] → Acceptable in-memory.
- [HTTP must pass retune times] → Infra wrap; Core does not edit `api/`.

## Migration Plan

None for data. `refine-sandbox-feedback/` removed; this directory is the Core sandbox change.

## Open Questions

None.
