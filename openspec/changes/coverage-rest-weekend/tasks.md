# Tasks

Implementation already on `master` (Core `8502a5e`, UI `50b7f29`). These tasks are the audit checklist.

## 1. Coverage leftover

- [x] 1.1 `derive_post_windows`: leftover live posts end at `max(last event, first departure)`, never `end = start`; MIDI remaining `[3]` at 16:00 → L3 10:30–16:00; slices include L3 after 10:30; stretch 4 h does not yield 14:30
- [x] 1.2 Evening leftover remaining `[3]` at 24:00 → L3 until 24:00; kitchen structures that close with `remaining ()` unchanged

## 2. Legal rest wrap

- [x] 2.1 `_legal_warnings` in `engine.py` and every vendored `engines/core_*.py`: skip pairs with day gap > 1, including cycle wrap; Saturday 24:00 + Monday 10:00 with Sunday empty → no `rest_between_days`
- [x] 2.2 Keep `test_cycle_wrap_rest_is_interdit` (Sunday → Monday adjacent); leave `_rest_between_ok` as day ±1

## 3. every_two at least one

- [x] 3.1 Evaluate miss only when neither weekend is fully off; empty assignments and two weekends off → no `weekend_every_two_weeks`; both weekends worked → still miss
- [x] 3.2 SAT `_build_rest_model`: `even_off + odd_off >= 1` in `engine.py` and vendored copies; `even` / `odd` unchanged

## 4. UI copy

- [x] 4.1 Recap title « Au moins un week-end / 14 j. », miss « aucun week-end complet off / 14 j. », radio / board « Au moins un we sur deux », release 0.61.0
