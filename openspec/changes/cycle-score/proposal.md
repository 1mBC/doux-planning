## Why

The restaurateur needs a single 0–10 reading of a published cycle (coverage, legal, contract, wellbeing, roles) without a second solve and without changing keep-best.

## What Changes

- Add `cycle_score(draft, result) -> CycleScore` and attach `score` on `cycle_recap` (same numbers).
- Five notes 0–10 one decimal, `null` when the denominator is missing. `global` = weighted mean 3 / 3 / 2 / 1.5 / 0.5 of non-null notes.
- Do not change `SEARCH_CALENDAR_LIMITS`, `SEARCH_SECONDS`, `_attempt_key`, or `generate_cycle` keep-best.
- Do not rewrite `saint-cloud.json`. No HTTP, no `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: cycle notes out of ten on recap / `cycle_score`.

## Impact

- `context.py` (`CycleScore`, `cycle_score`, `cycle_recap.score`), optional `_required_post_count` in `engine.py`. Tests for freeze scenarios. Do not edit `web/`, `api/`, `contracts/`, or the snapshot.
