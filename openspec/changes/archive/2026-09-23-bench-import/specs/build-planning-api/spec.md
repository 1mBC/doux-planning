# Spec Delta

## ADDED Requirements

### Requirement: Admin can preview a restaurant for bench import
`GET /v1/admin/restaurants/{restaurant_id}/import-preview` SHALL require a Bearer admin session. Success MUST be HTTP 200 with `restaurant_id`, `restaurant_name`, `email`, `salle` and `cuisine` objects each `{ ready, manuel_published, computes_published: { minimal, optimized, maximal } }`, and `generate_count`. `ready` MUST equal `team_ready` for that team. `manuel_published` MUST be true iff `versions.manuel` is non-null. `computes_published.*` MUST be true iff that effort slot is non-null. `generate_count` MUST be the number of `generate_logs` rows for that `restaurant_id`. An unknown company MUST be HTTP 404 `Restaurant introuvable.` A non-admin session MUST be HTTP 403 `Action réservée à l’admin.` Missing session MUST be HTTP 401. Without `DATABASE_URL` MUST be HTTP 503.

#### Scenario: Preview flags follow live state
- **WHEN** an admin previews a restaurant whose salle is team-ready, has a published manuel slot, a published minimal compute, and one generate log
- **THEN** `salle.ready` is true, `salle.manuel_published` is true, `salle.computes_published.minimal` is true, and `generate_count` is 1

#### Scenario: Unknown restaurant is 404
- **WHEN** an admin previews a restaurant id that does not exist
- **THEN** the response is HTTP 404 `Restaurant introuvable.`

### Requirement: Admin can import a restaurant as a bench dataset
`POST /v1/admin/bench/import` SHALL require a Bearer admin session and body `{ restaurant_id, include_salle?, include_cuisine?, include_manuel?, include_runs?, manual_score?, comment? }`. Omitted bool keys MUST default to true. `manual_score` when provided MUST be a finite number in `[0, 10]` stored as `round(x, 1)`; omitted or `null` means no override. `comment` MUST be trimmed; empty becomes null. Success MUST persist one `bench_imported_datasets` row (`category`/`origin` `imported`, opaque `imp-` + `token_urlsafe(8)` id) and return HTTP 200 `{ category: "imported", id, name, challenge_fr, origin: "imported", comment, manual_score_override, included: { salle, cuisine, manuel, runs } }`. Both teams false, a non-string/empty `restaurant_id`, or `manual_score` outside `[0, 10]` MUST be HTTP 400 `Champs invalides.` Unknown company MUST be HTTP 404 `Restaurant introuvable.` Non-admin MUST be HTTP 403. Missing session MUST be 401. Without `DATABASE_URL` MUST be 503. The live restaurant MUST NOT be mutated.

#### Scenario: Import with override lists as imported
- **WHEN** an admin imports a restaurant with `manual_score` 7.26
- **THEN** `GET /v1/admin/bench/versions` includes that dataset with `origin` `imported` and `manual.global` equal to 7.3

#### Scenario: include_runs copies salle computes
- **WHEN** an admin imports a restaurant that has a published salle minimal slot with `include_runs` true and `include_salle` true
- **THEN** `GET /versions` shows a last-run cell for that imported dataset’s minimal effort without a subsequent `POST /v1/admin/bench/run`

#### Scenario: Cuisine-only dataset cannot be run
- **WHEN** an admin imports with `include_salle` false and `include_cuisine` true then posts `scope=dataset` for that id
- **THEN** the response is HTTP 400 `Ce jeu n’a pas de salle.`

### Requirement: Versions list catalogue then imported with origin and comment
`GET /v1/admin/bench/versions` SHALL list catalogue datasets (disk order) then imported datasets (`created_at` desc). Every dataset MUST include `origin` (`catalogue` or `imported`) and `comment` (`null` for catalogue). Catalogue games MUST still load from disk. Worker `tick_bench_job` MUST load from disk, else from `bench_imported_datasets` via `bench_dataset_from_json` then `run_bench_on`; unknown MUST fail as today. Export `scope=dataset` MUST use the JSONB `context` for imported games. `POST` all/category/gaps MUST count imported salle games. Gaps MUST skip cuisine-only games.

#### Scenario: Halles stays a catalogue disk game
- **WHEN** an admin lists versions after an import
- **THEN** `tight`/`halles` is present with `origin` `catalogue` and `comment` null
