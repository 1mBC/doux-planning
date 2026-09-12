## 1. Load

- [x] 1.1 Add `list_bench_datasets` / `load_bench_dataset` / `UnknownBenchDataset` and verify four datasets list; incomplete folders are omitted; load halles is salle-ready and not cuisine-ready
- [x] 1.2 Evaluate expected assignments of all four datasets and verify zero `interdit`

## 2. Run

- [x] 2.1 Add `run_bench` (disposable copy, `generate_cycle`, `cycle_score` ×2, `deltas`) without writing `published_cycles`, and verify `run_bench("tight", "halles", minimal)` has `score`, `expected_score`, and `deltas`
- [x] 2.2 Verify a live `empty_restaurant` plus fiches is identical after `run_bench`, keep-best unchanged, and engine / recap pytest stay green

## 3. Crafted catalogue

- [x] 3.1 Add `crafted` to `BENCH_CATEGORY_ORDER` and verify `list_bench_datasets` returns the seven freeze pairs
- [x] 3.2 Verify expected of all seven has zero `interdit`; crafted atelier/rivoli/marais `cycle_score` global ≥ 9.5; `run_bench(tight, halles, minimal)` still green

## 4. Widen catalogue

- [x] 4.1 Extend `BENCH_CATEGORY_ORDER` and load `typical_week` from JSON when present, otherwise keep the derived week
- [x] 4.2 Add the 23 freeze folders (context + expected), leave the 7 existing files bit-identical, keep `VERSION` `core-2`
- [x] 4.3 Verify 30 listed pairs, every expected 0 `interdit`, six crafted global ≥ 9.5, coverage of morning / multi-type / L6, and `run_bench(tight, halles, minimal)` still green

## 5. Crafted oracles

- [x] 5.1 Add the 20 freeze `crafted` folders (grid first, then context), leave the 30 existing files bit-identical, keep `VERSION` `core-2`
- [x] 5.2 Verify 50 listed pairs, every expected 0 `interdit`, 26 crafted global ≥ 9.5, the 20 new have 0 `hours_miss` and 0 `below_role`, coverage of morning / multi-type / L6 among the 20, and `run_bench(tight, halles, minimal)` still green
