## Context

See proposal.md. `evaluate` already emits `empty_post` (coverage) and `max_*` / `max_coupures` (souhait). `cycle_recap` already builds wish rows from posed board wishes; cells are mostly OK / Non tenu. `week_label_scheme` stays `"parity"` / `"ab"` for the API. `format_clock` and `WEEKDAY_FR` already exist.

## Goals / Non-Goals

**Goals:**
- French `empty_post` and max-service / max-coupure warning text from `evaluate`.
- Wish recap cells that always show the measure (counts, days, radio value).

**Non-Goals:**
- Translating other warning codes (contrat anglais OK).
- Changing severities, `day_index` rules, or `week_label_scheme` API values.
- HTTP persist, snapshot rewrite, UI labels.

## Decisions

### 1. Shared FR helpers in `types.py`

`SERVICE_FR` plus week-label helpers that take weekend values (not `Employee`) so `engine` and `context` can share them without a cycle. `week_label_scheme(state)` still returns `"parity"` / `"ab"`.

### 2. Warning text only in `evaluate`

Same path as `rest_between_days`. Slice clocks come from `derive_slices` start/end. Weekdays for max services are the days in that week where the person has the service. Coupure text omits the day list (count + max + week only).

### 3. Wish measures in `_wish_row`

Reuse `_service_count` / `_coupure_count_in_week` for `nA` / `nB`. Pass draft hours so weekend rest day can treat a closed Sunday as `dim`. Max services and coupures share `max {limit} · {nA} / {nB} posés` (`OK · ` when held). Do not call `generate_cycle` to build recap tests — publish an evaluated draft.

## Risks / Trade-offs

- [Existing tests assert English `10:00` / generic max texts] → Update those assertions to the freeze FR form.
- [Closed Sunday looks like a held weekend rest day] → Same rule as `_has_weekend_rest_day`; document as intended.

## Migration Plan

None. Snapshot stays frozen. HTTP persist is Infra.

## Open Questions

None.
