# Design

## Context

See proposal.md. File 73 already parses `origin` on POST run and GET export. Freeze Infra of `contracts/domain/bench-export-speed.md` wins. Do not edit `contracts/`.

## Goals / Non-Goals

**Goals:**
- Dataset export = last-runs of every `engine_ref` for that couple, including copied import (`trace=null`).
- `GET /versions?origin=` filters listings and SQL runs before assembling the JSON.
- Versions path does not load `bench_runs.assignments` / `warnings` / `trace` nor imported `context`.

**Non-Goals:**
- Core rewrite. UI (`web/`). Alembic. Faster Stats without `origin`. Pagination. DELETE / import / impersonate / POST run origin semantics. `below_manuel` still VERSION-only.

## Decisions

### 1. Dataset pack reuses bank last-runs

`export_pack(scope=dataset)` looks up the listing (origin ignored), 404s if unknown, then `_latest_runs_by_quad()` + `_bank_pack_entry` (registry order then extras seen for that couple). `_latest_current_runs_map` stays only for `below_manuel`.

### 2. `_all_listings(origin)` skips the unused source

`catalogue` walks disk only (no `list_imported_rows`). `imported` reads imported listings only (no `list_bench_datasets`). Absent still unions both. Tombstones stay subtracted. POST run origin results stay the same.

### 3. Versions query uses `_parse_origin` and light rows

`admin_bench_versions` passes query `origin` into `list_versions`. Same parse as run/export. Runs: `defer` assignments/warnings/trace and filter `category` in SQL. Imported metadata: `defer(context)`. `engine_refs` = registre ∪ extras from those filtered runs.

## Risks / Trade-offs

- [Pre-existing Saint-Cloud / engine-ref pytest failures] → leave them.
- [Shared Postgres leftover `bench_runs`] → catalogue 0-run test deletes that couple’s rows first.

## Migration Plan

None. No Alembic.

## Open Questions

None.
