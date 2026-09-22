# Spec Delta

## ADDED Requirements

### Requirement: Solve a loaded bench dataset in memory
The system SHALL provide `run_bench_on(dataset, effort, engine_ref=None)` that runs the same salle-only generate, expected evaluate, deltas, and trace as `run_bench`, without writing `published_cycles`. `run_bench(category, id, effort, engine_ref)` MUST load that catalogue game then call `run_bench_on`. On a catalogue game the two paths MUST agree on category, id, effort, engine_ref, assignment count, generated global score, and expected global score. `load_bench_dataset`, `list_bench_datasets`, and the fifty catalogue files MUST stay unchanged.

#### Scenario: Halles minimal matches disk run
- **WHEN** `run_bench_on(load_bench_dataset("tight", "halles"), minimal)` and `run_bench("tight", "halles", minimal)` both complete
- **THEN** category, id, effort, engine_ref, assignment count, `score.global`, and `expected_score.global` are equal

#### Scenario: Catalogue count stays fifty
- **WHEN** `list_bench_datasets` is called
- **THEN** it still returns fifty entries

### Requirement: Hydrate a bench dataset from JSON
The system SHALL provide `bench_dataset_from_json(*, category, id, name, challenge_fr, context, assignments)` that reuses the same context hydrator as disk load and the existing shift hydrator. `assignments` MAY be an empty list; the resulting expected MUST be empty and MUST NOT raise. Employee `invite_token` in the context MUST be ignored. Both helpers MUST be importable from `doux_planning.bench`.

#### Scenario: Empty expected is valid
- **WHEN** `bench_dataset_from_json` is called with `assignments=[]` and a valid context object
- **THEN** it returns a dataset whose expected assignments are empty and does not raise
