## Why

A live restaurant starts empty. Before generate, the restaurateur must name the place, pick services, define named wave types, a typical week, and staff — and know whether **salle** is ready even if cuisine is not. That domain does not exist yet; Saint-Cloud is a frozen snapshot, not an empty onboarding path.

## What Changes

- `RestaurantIdentity` gains `name` (default `""`) and `legal_context_id` (default `"france"`). No copy of legal rules onto the restaurant.
- `empty_restaurant(restaurant_id)` returns a `RestaurantState` with no staff, no types, no company services, no typical week, no published cycle. `hours` is `None` until services are chosen. Saint-Cloud hydrate stays as-is.
- Named `ServiceType` (id, name, team, service_id, existing arrival/departure waves) plus `TypicalWeek` cells. `expand_typical_week` builds `ServiceStructure`s used identically for week A and week B.
- `team_ready(state, team)` follows the domain freeze (ladder, ≥1 fiche, ≥1 service, types for open services, typed open cells). No `generate_cycle`.
- Domain mutators: set name, set services, upsert type, set typical week, upsert fiche. No SQL persist, no HTTP.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: empty restaurant identity (name, legal context id), reuse of `Employee` / `RoleLadder`, `team_ready` staff/ladder checks.
- `service-structures`: zero or more company services; named types; typical week → identical 14-day structures; `team_ready` coverage checks.

## Impact

- `src/doux_planning/invites.py` (identity defaults), `src/doux_planning/structures.py` (types / typical week), new `src/doux_planning/context.py` (empty, expand, ready, mutators). `RestaurantState` gains optional context fields with harmless defaults.
- Tests for empty → ready salle-only, open cell without type, expand A = B, existing Saint-Cloud / pytest still green.
- Do not edit `web/`, `api/`, `contracts/`, `planning.py` preview/fill/undo, `engine.py` formulas, or `data/examples/saint-cloud.json`.
