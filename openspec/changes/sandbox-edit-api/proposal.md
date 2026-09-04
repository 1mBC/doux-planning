## Why

Core `refine-sandbox-feedback` changed occupied preview: retune is one timed trial, and each proposal carries `impact` plus before/after `_attempt_key` scores instead of a full warning delta. The HTTP wrap on `sandbox-edit-api` must follow the updated freeze in `contracts/http/v1-sandbox-edit.md` without a new mega-change.

## What Changes

- **BREAKING:** `POST /v1/sandbox/preview` with `gesture` `retune` requires `start_minutes` and `end_minutes` and calls `preview_retune(id, shift, start, end)` (0 or 1 proposal). Same hours → 400 French (`IdentityRetuneError`). Duration below min (or invalid grid) → 400 French.
- Replace/swap keep ranked lists. Proposals serialize `impact` (including `role_fit`) + `current_score` / `trial_score` (tuple `_attempt_key` → contract object). No `delta`, no trial-wide `warnings`, no `assignments`.
- Enter / GET sandbox add `score` of the open draft (`_attempt_key` on `last_result`). Adapter imports the engine helper; it MUST NOT rescore with a local formula.
- Commit retune re-calls `preview_retune` with the chosen hours (no enumerated-list match). Replace/swap matching unchanged. `partner` JSON includes all Shift fields (`day_index`, `weekday`, …).
- **BREAKING:** `history[]` recaps at commit from body + chosen proposal (`shift` or `slot`, hours, partner, impact). Undo pops. Persist recaps in Postgres.
- `POST /v1/sandbox/discard` wraps `discard_sandbox` then `enter_sandbox(..., "cycle")` (404 if never opened). Dual-read deletes then rewrites the session.



## Capabilities

### New Capabilities

- `sandbox-edit-http`: HTTP sandbox edit for the hydrated Saint-Cloud cycle (enter, preview, commit, undo), including compact impact/score feedback.

### Modified Capabilities

- (aucune — ne pas modifier `planning-examples` ni `build-planning-api`)

## Impact

`src/doux_planning/api/` (+ existing TestClient cases in `tests/test_preview_sandbox.py`). No edits to `planning.py` / `engine.py` / `hydrate.py` / `web/`. `build-planning-api` tasks 2–5 stay untouched.
