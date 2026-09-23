## Why

File 75. Three engine facts were wrong or too strict: a remaining bag after the last departure collapsed to a zero-length post (then stretched to 14:30); 11 h rest treated Saturday→Monday as adjacent across a closed Sunday; `every_two` required *exactly* one weekend off so an empty plan or two weekends off missed.

Code already landed Core `8502a5e` + UI `50b7f29` (v0.61.0). This change records the spec. It does not re-implement.

## What Changes

- Leftover live posts after the last wave keep covering every slice they are still in the remaining bag. They never leave before the first departure. Not “until restaurant close” if the bag already dropped them.
- `rest_between_days` only pairs calendar-adjacent worked days (including cycle wrap Sunday→Monday). A rest day in the middle (Sunday off) means no 11 h check on Saturday→Monday.
- `weekend: every_two` is **at least one** full weekend (sat+sun) off in 14 days. Two off is held. Empty plan is held. Miss only when both weekends have work. SAT rest: `even_off + odd_off >= 1`. `even` / `odd` unchanged.
- UI dictionary: title and miss line say at least one / none complete, not “exactly one”.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `service-structures`: last remaining bag may be non-empty; leftover posts last until that last wave, aligned with who is still listed.
- `constraint-engine`: leftover windows; 11 h only on adjacent days; every_two at-least-one; SAT allows both weekends off.
- `staff-configuration`: every_two wording is at least one weekend off / 14 j.
- `planning-ui`: recap / radio copy for every_two.

## Impact

- `coverage.py` `derive_post_windows` leftover end (already on master).
- `_legal_warnings` wrap and `_wellbeing_warnings` / `_build_rest_model` in `engine.py` and vendored `engines/core_*.py` (already on master).
- `web/src/scoreFacts.ts`, wizard radio, `mePlanning.ts`, release 0.61.0 (already on master).
- Tests in `test_coverage.py`, `test_engine.py`, `test_wellbeing.py` (already on master).
