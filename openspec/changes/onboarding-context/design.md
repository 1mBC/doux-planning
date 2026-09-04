## Context

See proposal.md. `RestaurantState` already holds employees, structures, hours, cycle. `RestaurantHours` rejects an empty service list. Saint-Cloud hydrate must keep passing filled `hours`. Do not call `generate_cycle`.

## Goals / Non-Goals

**Goals:**
- Empty onboarding graph in Python: identity, services, types, typical week, staff, `team_ready`.
- Expand typical week to `ServiceStructure` once; A and B share that result.

**Non-Goals:**
- HTTP, SQL, generate, publish, sandbox preview edits, second cycle.

## Decisions

### 1. New module `context.py`

Empty factory, `team_ready`, `expand_typical_week`, and mutators live in `src/doux_planning/context.py`. Types (`ServiceType`, `TypicalWeekCell`, `TypicalWeek`) live in `structures.py` beside the waves. `planning.py` only gains optional state fields — no preview/fill/undo edits.

### 2. `hours` is optional on `RestaurantState`

Empty restaurant uses `hours=None` and `company_services=()`. `set_services` writes `company_services` and, when the set is non-empty, a `RestaurantHours.multi_service(...)`. Saint-Cloud keep its existing `hours`; new fields default empty so hydrate is untouched.

### 3. Two typical-week grids via `team` on the cell

`TypicalWeekCell` includes `team` so salle and cuisine can be filled independently in one `TypicalWeek`. Closed cells need no `type_id`. Open services for a team = company services that have at least one non-closed cell for that team. `team_ready` also requires the typical week to exist and at least one open cell for that team.

### 4. Expand is weekday-named, not 14 copies

`expand_typical_week` groups open cells by `(team, service_id, type_id)` and emits one `ServiceStructure` per group. The same list is the engine input for days 0–6 and 7–13 (A = B). No second generate path.

### 5. Identity defaults

`RestaurantIdentity.name = ""`, `legal_context_id = "france"`. Existing positional/keyword constructors stay valid.

## Risks / Trade-offs

- [`as_draft` / sandbox on an empty restaurant would pass `hours=None`] → Accepted: generate/sandbox live is the next tranche; this change never calls them.
- [Saint-Cloud `team_ready` is false] → Accepted: hydrate is unchanged; existing tests do not call `team_ready`.

## Migration Plan

None for snapshot data. New fields default.

## Open Questions

None.
