## ADDED Requirements

### Requirement: Public Saint-Cloud snapshot matches live recap
The Saint-Cloud example file MUST store `planning.warnings` from `evaluate` on the file’s restaurant and assignments, and `planning.stats` / `legal_rows` / `wish_cols` / `wish_rows` from salle `cycle_recap` on that same draft and result. `restaurant`, `planning.assignments`, `search_effort`, `calendars`, and `seconds` MUST stay unchanged. The file MUST NOT call `generate_cycle` to refresh. `wish_cols` MUST use live keys and MUST NOT include `we1j`, `weA`, `weB`, `soirs`, `repos2`, or `coupures`. The file MUST NOT add `legal_cols`. `stats.assignments` MUST be 92, Théo Monday A midday MUST stay 660–960 / 5.0 h, and Diane `contrat` MUST stay `{ ok: false, text: "30h · 29h / 39h" }`. Warning messages MUST be French.

#### Scenario: Snapshot keeps the published grid
- **WHEN** the Saint-Cloud example file is read
- **THEN** it has 92 assignments, Théo Monday A midday is 11h–16h, and Diane `contrat` is `30h · 29h / 39h`

#### Scenario: Snapshot uses live wish keys and French warnings
- **WHEN** the Saint-Cloud example file is read
- **THEN** `wish_cols` has no `we1j` or `weA`, and at least one `contract_hours` and one `consecutive_rest_days` message contain `contrat` and `pas deux repos`
