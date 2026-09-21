## Context

See proposal.md. `upsert_employee` already replaces or appends a fiche. `UnknownEmployee` already exists in `invites.py` and is raised by `employee_board` and `redeem_invite`. `discard_live_sandbox` already sets `live_sandboxes[team]` to `None`. `redeem_invite` must stay byte-for-byte in behaviour so Infra can wrap it for re-link.

## Goals / Non-Goals

**Goals:**
- One Core mutation on `RestaurantState` that Infra can call after it nulls account FKs.
- Own-team unpublish + sandbox discard; other team untouched.

**Non-Goals:**
- HTTP, Alembic, accounts/sessions/email, engine formulas, `web/`, `contracts/`.
- Rewriting types, typical week, ladders, hours, or `week_label_scheme`.
- Changing `redeem_invite`.

## Decisions

### 1. `remove_employee` lives next to `upsert_employee`

`context.py` already mutates `RestaurantState` and returns it (`upsert_employee`, `generate_team`, `discard_live_sandbox`). Signature: `remove_employee(state, employee_id) -> RestaurantState`. Lookup the fiche; missing → `UnknownEmployee("Unknown employee")` (same message as `employee_board`). Drop from `state.employees`. `replace` the identity `linked_employee_ids` without that id. Set `published_cycles[team] = None` and call `discard_live_sandbox(state, team)` for the fiche’s team only.

Alternative: put the function in `invites.py` because `UnknownEmployee` lives there — rejected; the mutation is restaurant-state, not invite redeem.

### 2. No dedicated writes elsewhere

Do not clear `state.cycle` (Saint-Cloud toy), `state.accounts`, or the other team’s maps. A missing id in `linked_employee_ids` is a no-op (frozenset difference).

### 3. Tests stub both teams then enter salle live

Set up salle + cuisine fiches, mark both linked, attach a published cycle per team, `enter_live_sandbox` salle, then `remove_employee` of the salle id. A second test uses an unknown id. Do not change `redeem_invite` tests.

## Risks / Trade-offs

- [Solver-dependent dual generate] → Prefer attaching existing `PublishedCycle` objects (or `generate_team` with `SearchEffort.MINIMAL` if a real draft is easier) so the test does not depend on filling cuisine.
- [Shared dict mutation] → Same in-place pattern as `generate_team`; return the same `state`.

## Migration Plan

None. Infra consumes the function in a later change.

## Open Questions

None.
