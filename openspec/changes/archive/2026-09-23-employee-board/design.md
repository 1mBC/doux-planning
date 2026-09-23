## Context

See proposal.md. `published_cycles` and `generate_team` already exist. `employee_view` stays the Saint-Cloud own-shift helper. Do not read `live_sandboxes`. Do not call `generate_cycle` from the board.

## Goals / Non-Goals

**Goals:**
- Build `EmployeeBoard` from the fiche + `published_cycles[team]`.
- Map wellbeing prefs to existing souhait warning codes.

**Non-Goals:**
- HTTP `/v1/me/planning`, UI highlight, employee-authored edits, Saint-Cloud `legal_rows` / `wish_rows`.

## Decisions

### 1. `employee_board` lives in `context.py`

Same live-restaurant module as `generate_team`. Raises existing `UnknownEmployee`. Types `EmployeeBoard`, `BoardContract`, `BoardWish` sit next to it.

### 2. Contract `ok` uses published warnings

`weekly` = fiche hours. `assigned` = sum of that employee’s `duration_hours` on the published assignments (0 if none). When a published result exists, `ok` is true iff it has no `contract_hours` warning for that `employee_id`. When none exists, `ok` is `abs(0 - weekly) <= CONTRACT_HOUR_TOLERANCE`.

### 3. Wish mapping is a constant

`WellbeingPreference` → warning `code` as in the domain freeze. `held` is true when no `souhait` warning for that person and code. Iterate fiche prefs sorted by value for a stable tuple. Do not invent rows for prefs the fiche does not hold.

## Risks / Trade-offs

- [One-person salle generate] → Tests still assert board assignments equal the full published tuple, so colleagues are not filtered even if only one fiche generated.
- [Wish may or may not fire on minimal generate] → Tests derive `held` from the published warnings, not a hard-coded true/false.

## Migration Plan

None.

## Open Questions

None.
