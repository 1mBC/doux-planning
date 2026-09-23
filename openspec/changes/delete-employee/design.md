## Context

See proposal.md. `upsert_employee` already replaces or appends a fiche. `UnknownEmployee` already exists in `invites.py` and is raised by `employee_board` and `redeem_invite`. `discard_live_sandbox` already sets `live_sandboxes[team]` to `None`. `redeem_invite` must stay byte-for-byte in behaviour so Infra can wrap it for re-link. `_state_from_rows` does **not** hydrate `published_cycles` or `live_sandboxes`; `empty_restaurant` defaults both teams to `None`. Persisting those maps wholesale after `remove_employee` would wipe the other team.

## Goals / Non-Goals

**Goals:**
- One Core mutation on `RestaurantState` that Infra can call after it nulls account FKs.
- Own-team unpublish + sandbox discard; other team untouched.
- HTTP DELETE / link / nullable `me` affiliation; persist without `smash_live`.

**Non-Goals:**
- Rewriting types, typical week, ladders, hours, or `week_label_scheme`.
- Changing `redeem_invite`.
- UI, `engine.py` formulas, `contracts/`, cancel-job route, `cancelled` status, worker kill.
- Weakening PATCH omit of a still-linked fiche (stays 409).

## Decisions

### 1. `remove_employee` lives next to `upsert_employee`

`context.py` already mutates `RestaurantState` and returns it (`upsert_employee`, `generate_team`, `discard_live_sandbox`). Signature: `remove_employee(state, employee_id) -> RestaurantState`. Lookup the fiche; missing → `UnknownEmployee("Unknown employee")` (same message as `employee_board`). Drop from `state.employees`. `replace` the identity `linked_employee_ids` without that id. Set `published_cycles[team] = None` and call `discard_live_sandbox(state, team)` for the fiche’s team only.

Alternative: put the function in `invites.py` because `UnknownEmployee` lives there — rejected; the mutation is restaurant-state, not invite redeem.

### 2. No dedicated writes elsewhere (Core)

Do not clear `state.cycle` (Saint-Cloud toy), `state.accounts`, or the other team’s maps. A missing id in `linked_employee_ids` is a no-op (frozenset difference).

### 3. Tests stub both teams then enter salle live (Core)

Set up salle + cuisine fiches, mark both linked, attach a published cycle per team, `enter_live_sandbox` salle, then `remove_employee` of the salle id. A second test uses an unknown id. Do not change `redeem_invite` tests.

### 4. DELETE persist never uses `smash_live` (Infra)

`_persist_state(..., smash_live=True)` wipes **both** teams and deletes all employee accounts + emails. After `remove_employee`, in-memory `state.published_cycles` has both teams `None` even if cuisine is published in DB.

Correct DELETE persist:
1. Nullify affiliated `EmployeeAccountRow.restaurant_id` and `employee_id` together (never one without the other); delete that account’s `kind: employee` sessions; flush (FK before deleting the `staff_fiches` row).
2. `remove_employee` on the in-memory state.
3. `_persist_state` **without** `smash_live` (deletes fiche rows not in `keep`, writes `linked_employee_ids`).
4. On stored `company.published_cycles` JSON, set **only** `team.value` to `None`; keep the other key. Same for `company.live_sandboxes`. `flag_modified` both.

### 5. Link maps unknown fiche to 404, not register’s 400

`POST /v1/auth/link` wraps `redeem_invite(..., employee_id=..., employee_token=None)` with the existing `account_id`, then writes affiliation on **the same** row. Do not reuse `_map_invite_error` blindly: register maps `UnknownEmployee` → 400 `Champs invalides.`; link maps it → 404 `Fiche introuvable.` Leave register mapping unchanged. No `employee_token` on this endpoint.

### 6. Cheap maximal persist guard only

No cancel route, no `cancelled` status, no worker kill. In `persist_maximal_result`, if any assignment `employee_id` is not a current fiche, raise before `_persist_published` and mark the job failed with a French detail.

## Risks / Trade-offs

- [Solver-dependent dual generate] → Prefer attaching existing `PublishedCycle` objects (or `generate_team` with `SearchEffort.MINIMAL` if a real draft is easier) so the test does not depend on filling cuisine.
- [Shared dict mutation] → Same in-place pattern as `generate_team`; return the same `state`.
- [Hydration pitfall] → Never persist in-memory published/live maps after DELETE; patch stored JSON per team.

## Migration Plan

Alembic after `20260916_0014`: `employee_accounts.restaurant_id` and `employee_id` nullable, CHECK both-null or both-non-null; `sessions.restaurant_id` nullable. Composite FK MATCH SIMPLE allows both-NULL. Unique `(restaurant_id, employee_id)` allows multiple `(NULL, NULL)` in PostgreSQL. Do not drop `account_emails` uniqueness.

## Open Questions

None.
