## 1. Seed mutator

- [x] 1.1 Add `seed_example_context(state)` (types, typical week, ladders, new tokens, cleared published / live / cycle) and verify the freeze empty-restaurant and re-seed scenarios

## 2. Guardrails

- [x] 2.1 Run domain pytest green without calling `hydrate_delivered_cycle` / `generate_cycle` in the seed path and without editing `web/`, `api/`, `contracts/`, or `saint-cloud.json`
