## Context

See proposal.md. Legal rest 11h, two weekly rests, 5h coupure, 4h min shift, and contract tolerance stay as they are. `employee_view` and Saint-Cloud `state.sandbox` stay. Do not edit `api/` or `contracts/`.

## Goals / Non-Goals

**Goals:**
- Structured `Wellbeing` + exact `Unavailability` + `week_label_scheme`.
- Warnings and rest/fill solver aim at the same wishes.
- Hydrate new JSON only. Board wish rows `{ kind, held, … }`.

**Non-Goals:**
- HTTP persist, UI tabs, seed button, example HTTP contract edits.

## Decisions

### 1. `Wellbeing` on the fiche, not an enum set

`WeekendChoice` is `every_two` | `even` | `odd`. `max_services` is a mapping of present keys only. Default `Wellbeing()` is all-off. `Employee.max_evenings_per_week` / `max_mornings_per_week` are removed.

### 2. Consecutive rest uses circular weekdays and closed days

Pairs include Fri–Sat, Sat–Sun, Sun–Mon. A fully closed weekday counts as rest. Solver pair constraints use the same pairs.

### 3. Hydrate refuses legacy keys

A list `wellbeing`, deleted enum strings, `every_*` on indispos, or leftover `max_*_per_week` fields raise. Saint-Cloud employees are rewritten to the new object form.

### 4. Board mapping lives in this change

`BoardWish` uses `kind` plus optional `value` / `service_id` / `limit`. Held still means no matching published `souhait` code. Do not `/opsx-update` employee-board.

### 5. Recompute snapshot only if generate changes

Compare `generate_cycle(..., optimized)` assignments to the file. Identical → leave `planning`. Different → rewrite `planning` and report new stats; do not edit `contracts/http/v1-examples.md`.

### 6. Fill treats posed `max_services` as a hard cap (`core-1`)

If the key is present, a trial that would make that week's count (evaluate `_service_count` + the trial) exceed the limit is skipped like an overlap. It is no longer the 5th `_soft_penalty` tie-break. SAT rest, keep-best, `_attempt_key`, and `SEARCH_*` stay unchanged. Evaluate still emits `max_*` souhait facts.

### 7. Fill and repair use the same `fewest` window order (`core-2`)

`_fill_assignments` and `_repair_holes` share one job list. Eligible count is **static**: `_can_fill_window` on an empty assignment board (rest calendar + unavailabilities + hard `max_services` + legal), not already-placed shifts. Sort: `eligible_count` ascending, then `day_index`, then restaurant `hours.services` order, then post level descending (then `start_minutes` for stability). One strategy only — not `weekend-eve` or `eve-first`. Keep-best / `_attempt_key` / `SEARCH_*` stay unchanged.

### 8. Seeders lock windows, then SAT, then fill (`core-3`)

`generate_cycle` follows `contracts/domain/engine-seeds.md`. A seed is a list of lock `Shift`s. SAT forces `work[emp, day] = 1` on lock days and subtracts already-held posts from service coverage. Fill / repair / displace never move a lock. A locked seed that makes hard SAT infeasible is discarded (0 calendars, no slack). `empty` is the `core-2` pipe (one copy) and still slacks if hard SAT fails.

`SEED_TIGHT_THRESHOLD = 3`. Seeders: `tight-frozen` (eligibles once on an empty grid, seed only `≤ 3`, fewest first), `tight-dynamic` (recompute after each pose, next = tightest still `≤ 3`), `high-role` (L6…L1 then tension), `weekend-scarce` (Sat/Sun fewest, threshold 3), `empty`. Who to pose: legal → exact level → least versatile → furthest from contract hours → `employee_id`. Copies (10 / 50) permute tied windows and draw tied candidates via `seed_index`.

Compute: `SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` unchanged. `minimal` = empty + 16 calendars. `optimized` = 10 × each seeder except empty ×1, then 320 unique round-robin (1 / seed) / 30 s. `maximal` = 50 × + stop 10 min. Keep-best over every (seed × calendar).

### 9. Fill penalizes creating a coupure (`core-3`)

Drop `int(not started_day)` from `_soft_penalty`. Penalize a trial that creates a same-day coupure (already a shift that day **and** a gap). Prefer someone off that day, or a contiguous chain. Hard `max_coupures_per_week` skip stays. Fewest-first stays.

## Risks / Trade-offs

- [HTTP api still sends `wellbeing: []`] → Do not patch `api/`; list failing tests.
- [Sat–Sun now counts as consecutive rest] → Existing engine tests that assumed the opposite are updated to the freeze.

## Migration Plan

Snapshot employees this change. Persist/HTTP is the next Infra brief.

## Open Questions

None.
