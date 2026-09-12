## Purpose

Load the frozen salle bench datasets from disk (thirty games across ten categories) and run isolated generation against a human oracle, without touching a live restaurant or keep-best.

## ADDED Requirements

### Requirement: List and load bench datasets
The system SHALL scan `data/bench/{category}/{id}/` and list each dataset that has both `context.json` and `expected.json`. A folder missing either file MUST be omitted. `list_bench_datasets` MUST return `{ category, id, name, challenge_fr }` for each complete dataset in category order tight, clock, wishes, ladder, crafted, hours, size, overqual, closed, shapes (then id). `load_bench_dataset(category, id)` MUST build a disposable live restaurant context from `context.json` via services, role ladder, service types, typical week, and fiches, and MUST attach the oracle assignments from `expected.json`. After load, `team_ready(salle)` MUST be true and `team_ready(cuisine)` MUST be false. Unknown `(category, id)` MUST raise `UnknownBenchDataset`. Invite tokens MUST be generated at load and MUST differ from the employee id. When `typical_week` is present it MUST be used (one cell per team × service × weekday; several types may share a `service_id`). When it is absent the typical week MUST be derived: for each `roles.team` × `hours.services` × weekday, the cell is closed if the weekday is in `closed_weekdays`, otherwise `type_id` is the unique type for that `(team, service)`.

#### Scenario: Thirty complete datasets
- **WHEN** the repo contains the thirty frozen salle datasets
- **THEN** `list_bench_datasets` returns thirty entries in order tight, clock, wishes, ladder, crafted, hours, size, overqual, closed, shapes

#### Scenario: Stored typical week wins
- **WHEN** `context.json` includes `typical_week`
- **THEN** load uses those cells and may attach several types to the same service_id

#### Scenario: Derived typical week when omitted
- **WHEN** `context.json` has no `typical_week`
- **THEN** load derives one type per team × service as before

#### Scenario: Halles is salle-ready
- **WHEN** `load_bench_dataset("tight", "halles")` succeeds
- **THEN** `team_ready(salle)` is true and `team_ready(cuisine)` is false

#### Scenario: Incomplete dataset is omitted
- **WHEN** a category folder lacks `context.json` or `expected.json`
- **THEN** that dataset is absent from `list_bench_datasets`

### Requirement: Isolated bench run scores generated vs oracle
The system SHALL implement `run_bench(category, id, effort)` that loads a disposable copy, expands the typical week into a salle draft, calls `generate_cycle` with that effort, and computes `cycle_score` on the generated result and on the oracle assignments (same draft). `deltas[axe]` MUST be `note_generated − note_expected`, or `null` if either note is `null`, including `global`. The outcome MUST include `category`, `id`, `search_effort`, `duration_seconds`, `assignments`, `warnings`, `score`, `expected_score`, and `deltas`. `run_bench` MUST NOT write `published_cycles` on any live `RestaurantState`. Keep-best (`_attempt_key`, `SEARCH_*`, `generate_cycle`) MUST stay unchanged. Tests MUST use `minimal` only.

#### Scenario: Expected assignments have no interdit
- **WHEN** each listed dataset’s expected assignments is evaluated
- **THEN** there are zero `interdit` warnings

#### Scenario: Crafted witnesses score high
- **WHEN** `load_bench_dataset("crafted", id)` expected assignments are scored for each of the six crafted games
- **THEN** `cycle_score` global is at least 9.5

#### Scenario: Tight halles minimal run
- **WHEN** `run_bench("tight", "halles", minimal)` completes
- **THEN** the outcome has `score`, `expected_score`, and `deltas`

#### Scenario: Live restaurant unchanged
- **WHEN** `run_bench` is called while a live `RestaurantState` holds fiches
- **THEN** that state’s employees and `published_cycles` are identical afterwards
