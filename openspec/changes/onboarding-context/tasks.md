## 1. Empty restaurant and identity

- [x] 1.1 Add `name` / `legal_context_id` defaults and `empty_restaurant`, and verify an empty resto is not `team_ready` for either team and has no published cycle
- [x] 1.2 Add optional `RestaurantState` context fields (`hours` may be `None`, types, typical week, ladders, company services) without changing Saint-Cloud hydrate, and verify existing hydrate tests still pass

## 2. Types, typical week, ready

- [x] 2.1 Add `ServiceType` / `TypicalWeek` / mutators and `expand_typical_week`, and verify expanded structures for week A equal week B
- [x] 2.2 Implement `team_ready` per the freeze and verify salle-only complete path is ready, cuisine is not, and an open cell without a type makes salle not ready

## 3. Guardrails

- [x] 3.1 Run `pytest` green with no `generate_cycle` in this change and no edits to `web/`, `api/`, `contracts/`, preview/fill/undo, or engine formulas
