## 1. Retune single trial

- [x] 1.1 Change `preview_retune` to one `evaluate` of caller start/end (15 min, clip 0–1440, duration ≥ `min_shift_hours`) and verify ±15 on Théo 11:00–16:00 returns one proposal, draft unchanged
- [x] 1.2 Reject identity hours and sub-minimum duration (error or empty, not a success no-op) and verify tests cover both

## 2. Occupied ranking and impact

- [x] 2.1 Sort replace and swap by added interdits, added souhaits, hours-miss delta, then `_attempt_key`, and verify a replacement that adds only an interdit ranks before one that adds interdit + souhait
- [x] 2.2 Attach impact (new interdits, broken wishes, gesture-only contract closer/farther/excess, empty_post added/removed) plus current/trial `_attempt_key`, and verify an improved contract for A does not list unchanged B
- [x] 2.3 Leave `rank_candidates` empty-slot order unchanged and verify the existing occupancy-skip test still passes

## 3. Guardrails

- [x] 3.1 Keep `apply_proposal` / undo; verify apply of the single retune proposal crantes history
- [x] 3.2 Run `pytest` and verify it is green without edits to `api/`, `web/`, `contracts/`, FIFO / keep-best formulas, `generate_cycle`, `preview-sandbox-edits` artifacts, or the V0 archive

## 4. Role-fit impact

- [x] 4.1 Extend `PreviewImpact` / `preview_impact` with `role_fit` (gap = `employee.level - post_level` on gesture slots only) and verify L4→L2 on post 1 is `better` 3→1, inverse is `worse`, same level is empty, unchanged swap sum is empty, draft intact
## 5. Clicked-slot swap role_fit and empty fill

- [x] 5.1 Swap `role_fit` uses only the preview shift (not the partner) and verify L4 on post 1 swapped with L2 elsewhere is `better` 3→1, same level on the clicked post is empty
- [x] 5.2 Add `preview_fill` (structure span when hours omitted, occupied error, row person rank 1, others `occupied_sort_key`, empty `role_fit`) and verify empty Emma Monday midday, occupied reject, fill then undo
- [x] 5.3 Run `pytest` green without edits to `api/`, `web/`, `contracts/`, FIFO / keep-best / `generate_cycle` / `_overqualification` / `occupied_sort_key`
