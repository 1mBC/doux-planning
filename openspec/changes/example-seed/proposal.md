## Why

A live restaurant starts empty. Pré-BETA, every company account needs one domain call that fills context from the Saint-Cloud file (roles, team, types, typical week, hours, wishes, indispos) without copying the published planning or running generate.

## What Changes

- Add `seed_example_context(state)` that overwrites live context from `data/examples/saint-cloud.json` `restaurant` (employees, hours, structures).
- Map example structures to `ServiceType`s, a `TypicalWeek`, and `expand_typical_week` structures. Derive `ladders` from unique fiche roles on teams that appear.
- Mint a new `invite_token` per fiche (`≠ id`). Clear `published_cycles`, `live_sandboxes`, `cycle`, and `accounts`.
- Keep `identity.id`, `identity.name`, and `legal_context_id`. Do not copy the example restaurant name. Do not call `generate_cycle` or `hydrate_delivered_cycle`.
- No HTTP, no `web/`, no `api/`, no `contracts/`, no rewrite of `saint-cloud.json`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: seed fiches, ladders, and fresh invite tokens from the example file; keep identity name / id / legal context; empty published / live / cycle / accounts.
- `service-structures`: derive company services, hours, named types, and typical-week cells from example structures, then expand to engine structures.

## Impact

- `src/doux_planning/context.py` (new `seed_example_context`). Reuse hydrate parsers for the restaurant section only.
- Tests for the freeze seed scenarios plus existing domain pytest. Do not edit `web/`, `api/`, `contracts/`, `engine.py`, or `data/examples/saint-cloud.json`.
