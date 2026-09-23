## Context

See proposal.md. `empty_restaurant` and `expand_typical_week` already exist. Saint-Cloud JSON has hours + structures + employees, not `types` / `typical_week` / `ladders`. `hydrate_delivered_cycle` also installs a cycle and a snapshot sandbox — it must not be used here.

## Goals / Non-Goals

**Goals:**
- One mutator `seed_example_context(state)` that maps the file restaurant section onto live context fields and leaves identity / legal untouched.

**Non-Goals:**
- HTTP, JSON rewrite, generate, delivered-cycle hydrate, account smash.

## Decisions

### 1. Live in `context.py`, parse with hydrate helpers

`seed_example_context` sits next to `empty_restaurant`. It reads `data/examples/saint-cloud.json` via `data_dir()` and reuses `_hours` / `_structure` / `_employee` so wellbeing and indispos stay on the current form. It never calls `load_delivered_cycle` or `hydrate_delivered_cycle` (those pull `planning.assignments` and install a cycle).

### 2. Typical week covers every team × company service × weekday

Cells are built for both `Team` values and each service listed on example hours. A matching structure `(team, service_id)` whose `weekdays` contain the day → open + `type_id = structure.id`. Otherwise closed + `type_id` null. Cuisine therefore gets only closed cells on Saint-Cloud. First matching structure wins if two overlap (they do not on the current file).

### 3. Hours copied, not rebuilt via `set_services`

`set_services` would drop `closed_weekdays`. Seed copies example `hours` (Sunday closed, midday + evening) and sets `company_services` from `hours.services`. Each structure becomes a `ServiceType` with `name = id`. `state.structures = expand_typical_week(state)` after types and week are set.

### 4. Ladders from fiches; tokens from `Employee`

One `RoleLadder` per team that appears on example fiches; roles are unique `(name, level, team)` with `substitution_explained=True`. No cuisine ladder on Saint-Cloud. `_employee` omits `invite_token`, so `Employee` mints a fresh token (`≠ id`) on every seed. `published_cycles` / `live_sandboxes` reset to `{salle: None, cuisine: None}`; `cycle` and `accounts` emptied. Identity object is not replaced.

## Risks / Trade-offs

- [Private hydrate helpers] → Accepted: they already enforce the wellbeing freeze; no second parser.
- [Cuisine closed cells in the typical week] → Accepted: matches “every team × service × weekday”; `team_ready(cuisine)` stays false (no ladder, no fiche).

## Migration Plan

None. Domain-only mutator.

## Open Questions

None.
