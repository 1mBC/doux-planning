## Context

See `proposal.md`. Core now exposes `preview_retune(id, shift, start, end)`, `preview_fill(id, FillSlot, start|None, end|None)`, `OccupiedSlotError`, `IdentityRetuneError`, `PreviewImpact`, and `_attempt_key` scores. HTTP freeze: `contracts/http/v1-sandbox-edit.md`. Do not edit the engine. `GET /v1/examples/saint-cloud` stays the tranche-0 snapshot.

## Goals / Non-Goals

**Goals:**
- Wrap the new Python signatures 1:1 under `api/`.
- Wrap `discard_sandbox` + re-enter cycle; persist history recaps (not only the gesture name).

**Non-Goals:**
- Auth, jobs, week sandbox, React, copying `_attempt_key` arithmetic, inventing fields the Python types do not have.

## Decisions

### 1. Process-level store + optional Postgres overlay

Unchanged: one `PlanningStore`, hydrate only if Saint-Cloud is missing, history recaps in the API list (not in `planning.py`), `sandbox_sessions` when `DATABASE_URL` is set. Score is derived on read from `last_result`, not stored as a separate formula. Recaps are stored in the session document next to engine snapshots.

### 2. Retune is a timed trial; occupied lists still match; fill uses a slot

Preview/commit retune pass `start_minutes` and `end_minutes` into `preview_retune`. Commit takes that 0-or-1 list (no `proposal_id`, no scan of an enumerated ±2 h list). Replace still matches `employee_id`; swap still matches `partner` with engine shift equality.

Fill does **not** use `parse_shift`. Body `slot` is `FillSlot` (`employee_id`, `day_index`, `weekday`, `service_id`, `team`) plus `start_minutes` / `end_minutes` (both null/omitted → `None, None`; both ints → pass through; exactly one set → 400). Commit fill replays `preview_fill` and matches `employee_id`.

Alternative: keep matching retune by scanning a list. Rejected — Core no longer enumerates.

### 3. Errors

French `detail`. Catch `OccupiedSlotError` and `IdentityRetuneError` before generic `ValueError` (both subclass `ValueError`). Occupied fill → 409. Identity retune → 400. Closed service / duration below min / non-grid time → 400. Missing shift → 404. Missing gesture fields → 400. Empty undo → 409.

### 4. Serialization

Shift out: identity fields + `duration_hours` (`day_index` and `weekday` required on `partner`). Warnings only inside `impact.*`. `impact.role_fit` is the Python tuple as a JSON list (0 or 1 object: `current_gap`, `trial_gap`, `kind`). Do not recompute gaps in the adapter. Score object keys follow `_attempt_key` order: `empty`, `interdit`, `hours_miss`, `souhait`, `below_role`, `overqualification`. Import `_attempt_key`; zip onto those names. Do not invent extra score or impact keys.

### 5. History recap at commit; discard resets to the hydrated cycle

On commit, append a recap built from the request body plus the chosen proposal: occupied gestures copy `shift` (slot null); fill copies `slot` (shift null); `employee_id`, hours, `partner`, and `impact` come from the proposal. Undo pops that recap with the engine snapshot. Do not rescore.

`POST /v1/sandbox/discard` requires an open sandbox (404 otherwise), calls `discard_sandbox`, clears recaps, then `enter_sandbox(..., "cycle")`. With Postgres: delete the session row then persist the fresh draft.

Alternative: keep `{index, gesture}` only. Rejected — the overlay cannot re-read a cran.

## Risks / Trade-offs

- [hydrate_delivered_cycle always discards] → Call it only when the restaurant is absent.
- [TestClient store leak] → Reset runtime in tests.
- [Temptation to copy score math] → Import `_attempt_key` only.

## Migration Plan

No new table. Existing `sandbox_sessions` rows still restore assignments/history; `score` is recomputed from `last_result`.

## Open Questions

None. Contract wins on shape.
