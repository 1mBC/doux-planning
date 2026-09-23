# Tasks

## 1. Live recap on generated assignments

- [x] 1.1 `run_bench_on`: after `generate_for`, `evaluate(draft.with_assignments(result.assignments))` then `cycle_recap_from_draft`; `outcome.score` / `facts` / `warnings` from that recap; `assignments` stay generated; `engine_ref` stays requested
- [x] 1.2 Oracle path unchanged (already live `evaluate`). mix-0 picker unchanged. No `api/` / `web/` / leftover / vendored evaluate edits

## 2. Tests

- [x] 2.1 `run_bench_on` `core-2` and `mix-0` `minimal` on a catalogue game: persisted-side `global_score` equals live recap of `outcome.assignments`
- [x] 2.2 Existing `test_bench.py` / engine pytest stay green
