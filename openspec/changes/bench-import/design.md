# Design

## Context

See proposal.md. `run_bench` in `src/doux_planning/bench.py` loads a disk dataset then generates salle-only against the oracle. Infra will later pass a snapshot that never existed under `data/bench/`. Freeze Core of `contracts/domain/bench-import.md` wins. `_load_context` already hydrates multi-team JSON; `_employee` already omits `invite_token`.

## Goals / Non-Goals

**Goals:**
- One in-memory solve entry (`run_bench_on`) shared by disk `run_bench` and future imported rows.
- JSON → `BenchDataset` without touching the catalogue scanner.

**Non-Goals:**
- HTTP import, `bench_imported_datasets`, worker `tick_bench_job` DB fallback, versions `origin` field.
- Rewriting `load_bench_dataset` / `list_bench_datasets` or any `data/bench/` file.
- Manual-score override (Infra applies that after persist).

## Decisions

### 1. Extract the current body, keep `run_bench` as a thin load wrapper

Move the generate/evaluate block into `run_bench_on(dataset, effort, engine_ref=None)`. `run_bench` calls `load_bench_dataset` then `run_bench_on`. Outcome identity fields come from `dataset.category` / `dataset.id`. Engine ref resolution stays inside `run_bench_on` so an imported dataset can pin a ref without going through disk load.

Alternative: duplicate the body for imported games — rejected; freeze wants one extract.

### 2. Hydrate JSON with `_load_context` + `_shift`

`bench_dataset_from_json` keyword-only args match the freeze. Restaurant state comes from `_load_context(category, id, context)` (same restaurant id scheme `bench-{category}-{id}`). Expected is `tuple(_shift(item) for item in assignments)` so `[]` is `()`. Dataset `name` / `challenge_fr` are the kwargs, not re-read from context, so Infra can set comment-derived challenge independently of snapshot `name`.

`invite_token` is omitted by copying each employee dict without that key before `_load_context`; `_employee` already ignores extra keys.

Alternative: parse a new hydrator — rejected; freeze says reuse.

### 3. Tests compare stable outcome fields only

Two independent generates may differ in `duration_seconds`. Compare category, id, effort, engine_ref, assignment count, `score.global_score`, `expected_score.global_score`. Empty-assignments test uses a copied halles `context.json` (read-only). Catalogue count 50 already covered; keep that assertion.

## Risks / Trade-offs

- [Two halles minimal generates in one test] → use MINIMAL only; compare scores not duration.
- [Empty expected evaluate] → same path as today (`evaluate` on empty assignments); assert no raise.

## Migration Plan

No schema or caller migration. Existing `run_bench(...)` call sites keep working. Infra imports the new names in a later slice.

## Open Questions

None.
