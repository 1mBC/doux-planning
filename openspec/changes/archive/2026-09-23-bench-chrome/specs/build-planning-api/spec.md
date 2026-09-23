# Spec Delta

## ADDED Requirements

### Requirement: Admin can delete a bench dataset
`DELETE /v1/admin/bench/datasets/{category}/{dataset_id}` SHALL require a Bearer admin session. Success MUST be HTTP 204 with an empty body.

When `category` is `imported` and a `bench_imported_datasets` row exists for that id, the system MUST delete that row and MUST delete every `bench_runs` and `bench_jobs` row with the same `(category, dataset_id)`. Catalogue files MUST NOT be written.

When the pair matches a catalogue game still on disk, the system MUST NOT delete those files. It MUST insert `bench_tombstones (category, dataset_id)` (primary key the couple) if missing, and MUST delete every `bench_runs` and `bench_jobs` row for that couple. A second DELETE of an already-tombstoned catalogue game MUST be HTTP 204 (idempotent).

When the pair is not on disk, not an imported row, and not already tombstoned, the response MUST be HTTP 404 `Jeu introuvable.` A non-admin session MUST be HTTP 403 `Action réservée à l’admin.` Missing session MUST be HTTP 401. Without `DATABASE_URL` MUST be HTTP 503.

#### Scenario: Delete an imported restaurant game
- **WHEN** an admin imports a restaurant then DELETEs that `imported` dataset
- **THEN** the response is HTTP 204, the dataset is absent from `GET /v1/admin/bench/versions`, and zero `bench_runs` and `bench_jobs` remain for that id

#### Scenario: Tombstone a catalogue game
- **WHEN** an admin DELETEs `tight` / `halles`
- **THEN** the response is HTTP 204, `halles` is absent from `GET /v1/admin/bench/versions`, the folder `data/bench/tight/halles` still exists on disk, and a second DELETE is HTTP 204

#### Scenario: Unknown dataset is 404
- **WHEN** an admin DELETEs a pair that is not on disk, not imported, and not tombstoned
- **THEN** the response is HTTP 404 `Jeu introuvable.`

#### Scenario: Non-admin cannot delete
- **WHEN** a company session with `admin` false DELETEs a bench dataset
- **THEN** the response is HTTP 403 `Action réservée à l’admin.`

### Requirement: Tombstoned datasets are excluded from listing and enqueue
`GET /v1/admin/bench/versions`, `GET /v1/admin/bench/datasets`, export, `POST /v1/admin/bench/run` with `scope=all`, `scope=category`, `scope=gaps`, and known-target resolution SHALL omit tombstoned `(category, dataset_id)` pairs. Imported datasets that were not deleted MUST still be listed. Catalogue files MAY remain on disk; once tombstoned they MUST NOT appear. No new JSON keys beyond those already emitted (`origin` from file 71).

#### Scenario: Gaps skip a tombstoned catalogue game
- **WHEN** `tight` / `halles` is tombstoned and an admin posts `scope=gaps`
- **THEN** the queued jobs do not include `halles`
