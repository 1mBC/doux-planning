# Design

## Context

See proposal.md and freeze `contracts/domain/bench-score-live.md`. `GET /compare` and `GET /runs/{id}` already rebuild `CycleSlice` via `_cycle_slice` → live `evaluate` + `cycle_recap_from_draft`. `GET /versions` cells use persisted `BenchRun.score` and must stay light (no assignments). `run_bench_on` today recaps the generator `EngineResult` (frozen-engine warnings). mix-0 returns the winner’s vendored warnings. Those two notes diverge after scoring-rule changes (file 75 leftover / wrap / every_two).

## Goals / Non-Goals

**Goals:**
- A newly persisted bench run’s `score.global` equals the run-page live recap of the same assignments.
- Table cell updates after a re-run because persist writes that live recap.

**Non-Goals:**
- Recompute `GET /versions` from assignments (file 74).
- Show absolute /10 on the table (delta ×10 stays).
- Rescore rows already in Postgres without a new run.
- Change mix-0 expert picking.
- Infra HTTP, UI, leftover windows, legal formulas.

## Decisions

### 1. Live evaluate on the generated side, same as oracle

Oracle already does `evaluate(expected_draft)` then recap. Generated side must do the same with `result.assignments`. Assignments stored are still `generate_for` output. Warnings/facts/score stored are the live recap.

### 2. Versions stay a snapshot

Infra keeps `cell.global = row.score.global`. Correct persist is enough. No Alembic.

### 3. mix-0 picker stays internal

`mix_0.generate_cycle` may still rank experts with `cycle_score(draft, expert_result)`. Only `run_bench_on` re-evaluates the winner grid for the recorded note.

## Risks / Trade-offs

- Old `bench_runs` stay on generator-era scores until the admin re-runs that cell. Accepted.
- Live `evaluate` vs vendored generate can still pick the same grid and a different note; that is intended (one scoring function for the banc).
