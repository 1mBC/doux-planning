# Spec Delta

## MODIFIED Requirements

### Requirement: Isolated bench run scores generated vs oracle
The system SHALL implement `run_bench(category, id, effort, engine_ref=None)` that loads a disposable copy, expands the typical week into a salle draft, calls `generate_for` with that effort and ref (omitted ref = `VERSION`), and computes recap scores on the **live `evaluate` of the generated assignments** and on the oracle assignments (same draft; oracle already live-evaluates). The generated-side recap MUST NOT use the generator’s `result.warnings` as the scoring source. `deltas[axe]` MUST be `note_generated − note_expected`, or `null` if either note is `null`, including `global`. The outcome MUST include `category`, `id`, `search_effort`, `duration_seconds`, `assignments` (the generated shifts), `warnings` (from live evaluate), `score` (from that live recap), `expected_score`, `deltas`, `engine_ref` (the requested ref), and `trace`. `run_bench` MUST NOT write `published_cycles` on any live `RestaurantState`. Keep-best (`_attempt_key`, `SEARCH_*`, seeds) MUST stay unchanged. Tests MUST use `minimal` only.

#### Scenario: Expected assignments have no interdit
- **WHEN** each listed dataset’s expected assignments is evaluated
- **THEN** there are zero `interdit` warnings

#### Scenario: Crafted witnesses score high
- **WHEN** `load_bench_dataset("crafted", id)` expected assignments are scored for each of the 26 crafted games
- **THEN** `cycle_score` global is at least 9.5

#### Scenario: New crafted oracles match hours and role
- **WHEN** each of the 20 new crafted expected grids is evaluated
- **THEN** hours miss is 0 and below_role is 0

#### Scenario: Tight halles minimal run
- **WHEN** `run_bench("tight", "halles", minimal)` completes
- **THEN** the outcome has `score`, `expected_score`, `deltas`, and a complete `trace`

#### Scenario: Replay a vendored engine
- **WHEN** `run_bench("tight", "halles", minimal, engine_ref="core-2")` completes
- **THEN** `outcome.engine_ref` is `core-2`, `trace.seeder` is `empty`, and `trace.n_locks` is 0

#### Scenario: Generated score matches live evaluate of stored shifts
- **WHEN** `run_bench_on` completes for `engine_ref` `core-2` and for `mix-0` on a catalogue game at `minimal`
- **THEN** `outcome.score.global_score` equals `cycle_recap_from_draft` of live `evaluate` of `outcome.assignments`

#### Scenario: Unknown engine ref
- **WHEN** `generate_for` is called with a ref not in `list_engine_refs`
- **THEN** it raises `UnknownEngineRef`

#### Scenario: Live restaurant unchanged
- **WHEN** `run_bench` is called while a live `RestaurantState` holds fiches
- **THEN** that state’s employees and `published_cycles` are identical afterwards
