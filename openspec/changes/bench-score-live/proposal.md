# Proposal

## Why

On the bench, re-running mix-0 updates the saved shifts (click-to-view shows the new grid) but the table cell stays on the old note, while the run page score goes up. The table reads `bench_runs.score` frozen from the generator’s warnings (mix-0 winner = vendored evaluate). The run page re-scores with live `engine.py` `evaluate`. File 76 freeze `contracts/domain/bench-score-live.md` wins. Core only.

## What Changes

- `run_bench_on` scores the generated cycle with live `evaluate` + `cycle_recap_from_draft` of the generated assignments — the same path as `GET /runs/{id}` `model.score`.
- Persist still stores that recap JSON; `GET /versions` still reads it (file 74 light cells). A new run updates the cell.
- `engine_ref` stays the requested ref. mix-0 expert picker unchanged. Oracle side already live-evaluates.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `bench-datasets`: generated-side recap uses live `evaluate` of generated assignments, not generator `result.warnings`.

## Impact

- Core: `src/doux_planning/bench.py` `run_bench_on` only.
- Tests in `tests/test_bench.py`.
- Do not edit `web/`, `api/`, `contracts/`, `engine.py` formulas, leftover, mix-0 picker, Alembic.
