# Design

## Context

See proposal.md and freeze `contracts/domain/coverage-rest-weekend.md`. Implementation is already on `master` (Core `8502a5e`, UI `50b7f29`). This design describes that code so OpenSpec matches production.

`derive_post_windows` used to close leftover live posts with `end_minutes = start_minutes`. `stretch_to_min_shift` then grew a 0-length L3 MIDI window 10:30–14:30 while the first departure was 15:30. `_legal_warnings` wrapped last-worked → first-worked with the adjacent-day rest formula even when a rest day sat in between. `EVERY_TWO` missed when `off_even == off_odd` (both off or both on). SAT forced `even_off + odd_off == 1`.

## Goals / Non-Goals

**Goals:**
- Leftover posts follow the remaining bag (floor: first departure).
- 11 h only on adjacent worked days, wrap included.
- every_two = at least one full weekend off.
- Specs and UI copy match.

**Non-Goals:**
- Forcing the last remaining bag to `[]`.
- Changing `_rest_between_ok` (still day ±1 only).
- Changing `even` / `odd`.
- Re-running generation of LE GARDE MANGER in this change.

## Decisions

### 1. Leftover end is last wave, floored by first departure

After the event loop, still-live posts end at `max(last event, first departure, start)`. That is the last clock they were still in the bag. Slices then include them. `stretch_to_min_shift` is unchanged.

### 2. Wrap rest skips a gap greater than one day

`if day_b_raw - day_a > 1: continue` with no wrap exception. Sunday 14h–23h → Monday 8h–16h (gap 1) still interdit.

### 3. At-least-one weekend, SAT `>= 1`

Evaluate misses only when neither weekend is fully off. Solver may leave both off.

## Risks / Trade-offs

- Types that never close the bag keep the leftover person until the last named clock (often 16:00 / 24:00). That is intended alignment with remaining, not restaurant closing hours.
- Vendored evaluate copies must stay in lockstep (already patched together).
