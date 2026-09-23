# Spec Delta

## ADDED Requirements

### Requirement: SPA serves Banc Manuels
When `web/dist/index.html` is present, FastAPI MUST serve that file for `GET /admin/bench/manuels` the same way as `GET /admin/bench`.

#### Scenario: Manuels path serves index
- **WHEN** `web/dist` exists and a client GETs `/admin/bench/manuels`
- **THEN** the response is HTTP 200 with the same `index.html` body as `/admin/bench`

### Requirement: Bench run and export accept an origin filter
`origin` SHALL be optional and MUST be `"catalogue"` or `"imported"` when present. Absent, JSON `null`, or `""` MUST mean no origin filter (catalogue and imported, current behaviour). Any other value MUST be HTTP 400 `Champs invalides.`

`POST /v1/admin/bench/run` MAY include `origin` in the body. For `scope=all`, `scope=category`, and `scope=gaps`, targets MUST come from `_known_targets` / `_gap_targets` / `_all_listings` filtered by that origin: `catalogue` is listings that are not imported (`origin=catalogue`, not `category=imported`); `imported` is imported listings only. Tombstones MUST stay excluded. Cuisine-only imported MUST stay excluded from all/gaps and MUST stay HTTP 400 `Ce jeu n’a pas de salle.` on `scope=dataset`. `scope=dataset` MUST ignore `origin` if present. `scope=category` plus an origin that does not cover that category MUST enqueue an empty target list (not 400).

`GET /v1/admin/bench/export` MAY take query `origin` with the same semantics for `scope=below_manuel` and `scope=bank`. `scope=dataset` MUST ignore origin. `GET /v1/admin/bench/versions` MUST stay unfiltered by origin. Non-admin MUST stay HTTP 403 `Action réservée à l’admin.`

#### Scenario: Catalogue all skips imported jobs
- **WHEN** an admin has imported a restaurant and posts `scope=all` with `origin=catalogue`
- **THEN** none of the queued jobs have `category=imported`

#### Scenario: Imported all skips catalogue games
- **WHEN** an admin has imported a restaurant and posts `scope=all` with `origin=imported`
- **THEN** none of the queued jobs are catalogue games

#### Scenario: Catalogue gaps skip imported jobs
- **WHEN** an admin posts `scope=gaps` with `origin=catalogue` after an import
- **THEN** none of the queued jobs are imported

#### Scenario: Missing origin keeps both origins
- **WHEN** an admin posts `scope=all` or `scope=gaps` without an `origin` key after an import
- **THEN** the queued jobs include both catalogue and imported games

#### Scenario: Unknown origin is 400
- **WHEN** an admin posts or exports with `origin=nope`
- **THEN** the response is HTTP 400 `Champs invalides.`

#### Scenario: Bank export catalogue omits imported datasets
- **WHEN** an admin GETs `/v1/admin/bench/export?scope=bank&origin=catalogue` after an import
- **THEN** the pack has no dataset with `category=imported`

#### Scenario: Non-admin cannot run or export with origin
- **WHEN** a company session with `admin` false posts run or GETs export with `origin=catalogue`
- **THEN** the response is HTTP 403 `Action réservée à l’admin.`
