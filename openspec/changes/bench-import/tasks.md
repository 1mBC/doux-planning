# Tasks

## 1. Extract solve

- [ ] 1.1 Extract `run_bench_on(dataset, effort, engine_ref=None)` from the current `run_bench` body (salle-only, no `published_cycles` write, evaluate expected, deltas, trace) and make `run_bench` load then delegate; verify `run_bench_on(load_bench_dataset("tight","halles"), MINIMAL)` matches `run_bench(...)` on category, id, effort, engine_ref, assignment count, score.global, expected_score.global
- [ ] 1.2 Add `bench_dataset_from_json(*, category, id, name, challenge_fr, context, assignments)` reusing `_load_context` and `_shift`, omit employee `invite_token`, export both helpers from `doux_planning.bench`; verify `assignments=[]` returns empty expected without raising

## 2. Catalogue guard

- [ ] 2.1 Keep `load_bench_dataset` / `list_bench_datasets` behaviour and do not rewrite `data/bench/` files; verify `list_bench_datasets` still has 50 entries and Core pytest for the new tests is green
