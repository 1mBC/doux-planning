## Context

See proposal.md. Occupied previews already call `evaluate` / `rank_candidates` / `swap_shifts`. `_attempt_key` and `_hours_miss` already exist in `engine.py`. Do not change those functions’ formulas. Do not edit `preview-sandbox-edits` artifacts or `api/`.

## Goals / Non-Goals

**Goals:**
- One-shot retune trial with explicit times.
- Occupied list order from delta + hours-miss change + existing `_attempt_key`.
- Compact `PreviewImpact` (clicked-slot `role_fit`) + before/after score on each proposal.
- Empty-cell `preview_fill` with structure-span default hours.

**Non-Goals:**
- HTTP / overlay / a second local scorer / changing empty-slot `rank_candidates` / FIFO / `generate_cycle` / `_overqualification` / `_below_role_count` / changing `occupied_sort_key` (fill **uses** it to rank non-row candidates).

## Decisions

### 1. Retune signature takes start and end

`preview_retune(restaurant_id, shift, start_minutes, end_minutes) -> list[PreviewProposal]` with length 0 or 1. Clip to `[0, 1440]`, require 15-minute grid via `validate_quantum`, duration ≥ `min_shift_hours`. Identity (clipped times equal current) raises `IdentityRetuneError`. Invalid duration / grid raises `ValueError`. Still a list so apply/undo stay list-shaped. No enumeration helper.

### 2. Occupied rank uses `rank_candidates` / `swap_shifts` only to build trials

Keep eligibility (drop holder, skip overlapping, skip own shifts). Re-sort with `(added_interdit, added_souhait, hours_miss_trial - hours_miss_current, _attempt_key(draft, trial), tie-break)`. Import `_attempt_key` and `_hours_miss`; do not copy the arithmetic.

### 3. Impact filters the existing warning delta

`new_interdits` = added + interdit. `broken_wishes` = added + souhait except `contract_hours`. Coverage = added/removed with code `empty_post`. Contract rows: weekly hours for gesture employee ids only, weeks 0 and 7; omit a row if hours did not change; `excess` if trial hours > contract + 0.5; else `closer` / `farther` by absolute distance to contract. Messages on warning items stay engine text.

`role_fit` is 0 or 1 row on `PreviewImpact`. Gap = `employee.level - post_level` (same term as `_overqualification`, do not call or copy that function) on the **clicked slot only**: retune / replace / swap = the preview `shift`, not the swap partner. Fill has no current occupant → empty. Missing occupant → omit. `kind` is `better` if trial < current, `worse` if trial > current; equal → empty tuple. No French copy. Do not change `occupied_sort_key`.

### 4. Score fields are `_attempt_key` tuples

`current_score` and `trial_score` on `PreviewProposal`. Same six-tuple as generation keep-best.

### 5. Empty cell is `preview_fill`

`preview_fill(restaurant_id, slot, start_minutes | None, end_minutes | None)`. Slot identifies the **row** (`employee_id`, `day_index`, `weekday`, `service_id`, `team`). Both times omitted → first arrival to last departure of `structure_for` that team/service/weekday; closed / missing structure raises `ValueError`. Explicit times: clip 0–1440, 15-minute grid, duration ≥ the row person’s `min_shift_hours`. `post_level` = that person’s `role.level` for every candidate. An existing assignment for row × day × service raises `OccupiedSlotError`. One `evaluate` per eligible candidate (append a shift; skip team mismatch, `level < post_level`, overlapping occupancy). Rank 1 = the row person when eligible; remaining candidates sorted with `occupied_sort_key` (do not modify that function). `gesture` `"fill"`, `employee_id` = the candidate, `start_minutes` / `end_minutes` set, `role_fit` empty. Draft unchanged. `apply_proposal` / undo unchanged.

## Risks / Trade-offs

- [HTTP `preview_retune(shift)` will TypeError until Infra passes times] → Accepted: Core must not edit `api/`.
- [Breaking existing preview tests that enumerate ±2 h] → Update `tests/test_preview_sandbox.py` only.

## Migration Plan

None for data. Infra follows with HTTP after Python tests are green.

## Open Questions

None.
