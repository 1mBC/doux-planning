# Spec Delta

## ADDED Requirements

### Requirement: Dataset export includes last-runs of every engine_ref
`GET /v1/admin/bench/export?scope=dataset` SHALL export last-runs of **all** `engine_ref` for that `(category, dataset_id)` (same effort packing as `scope=bank` for one listing). It MUST NOT use `_latest_current_runs_map`. Copied import runs (`trace` null, `app_version` = restaurant slot `engine_ref`) MUST be included when they are the last-run of that `(engine_ref, search_effort)`. Query `origin` MUST stay ignored after validation. Unknown listing MUST be HTTP 404 `Jeu introuvable.` A known listing with zero `bench_runs` rows MUST be HTTP 404 `Aucun run pour ce jeu.` `scope=below_manuel` MUST stay last-run of the current VERSION only. Non-admin MUST stay HTTP 403 `Action réservée à l’admin.`

#### Scenario: Imported copied runs whose engine_ref is not VERSION export
- **WHEN** an admin imports a restaurant that has published salle computes whose `engine_ref` is not the current VERSION and does not re-run VERSION on that game
- **THEN** `GET /v1/admin/bench/export?scope=dataset&category=imported&dataset_id=` is HTTP 200, `datasets[0].efforts` is non-empty, and at least one effort has `engine_ref` other than VERSION

#### Scenario: Catalogue game with zero runs is 404
- **WHEN** an admin GETs `scope=dataset` for a catalogue listing that has zero `bench_runs` rows
- **THEN** the response is HTTP 404 `Aucun run pour ce jeu.`

### Requirement: GET versions accepts an origin filter
`GET /v1/admin/bench/versions` MAY take query `origin`. `"catalogue"` and `"imported"` MUST filter both listings and `bench_runs` before assembling the payload. Absent, JSON `null`, or `""` MUST keep the current union (catalogue then imported) for Stats. Any other value MUST be HTTP 400 `Champs invalides.` `origin=catalogue` MUST NOT call `list_imported_rows` / load imported context and MUST SQL-filter `bench_runs.category != 'imported'`. `origin=imported` MUST NOT call `list_bench_datasets` / walk `data/bench/**` and MUST SQL-filter `category = 'imported'`. JSON keys MUST stay unchanged. `engine_refs` MUST be the full `list_engine_refs()` union extras seen in the **filtered** runs. This path MUST NOT load `bench_runs.assignments`, `warnings`, or `trace`, and MUST NOT load `bench_imported_datasets.context`. Non-admin MUST stay HTTP 403 `Action réservée à l’admin.`

#### Scenario: Imported origin omits catalogue datasets
- **WHEN** an admin GETs `/v1/admin/bench/versions?origin=imported` after an import
- **THEN** no dataset has `origin=catalogue`

#### Scenario: Catalogue origin omits imported datasets
- **WHEN** an admin GETs `/v1/admin/bench/versions?origin=catalogue` after an import
- **THEN** no dataset has `origin=imported`

#### Scenario: Missing origin keeps both origins
- **WHEN** an admin GETs `/v1/admin/bench/versions` without an `origin` query after an import
- **THEN** the datasets include both `origin=catalogue` and `origin=imported`

#### Scenario: Unknown origin is 400
- **WHEN** an admin GETs `/v1/admin/bench/versions?origin=nope`
- **THEN** the response is HTTP 400 `Champs invalides.`

#### Scenario: Non-admin cannot read versions
- **WHEN** a company session with `admin` false GETs `/v1/admin/bench/versions` or `/v1/admin/bench/export?scope=dataset`
- **THEN** the response is HTTP 403 `Action réservée à l’admin.`
