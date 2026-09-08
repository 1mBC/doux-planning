## 1. Load

- [x] 1.1 Add `list_bench_datasets` / `load_bench_dataset` / `UnknownBenchDataset` and verify four datasets list; incomplete folders are omitted; load halles is salle-ready and not cuisine-ready
- [x] 1.2 Evaluate expected assignments of all four datasets and verify zero `interdit`

## 2. Run

- [x] 2.1 Add `run_bench` (disposable copy, `generate_cycle`, `cycle_score` ×2, `deltas`) without writing `published_cycles`, and verify `run_bench("tight", "halles", minimal)` has `score`, `expected_score`, and `deltas`
- [x] 2.2 Verify a live `empty_restaurant` plus fiches is identical after `run_bench`, keep-best unchanged, and engine / recap pytest stay green
