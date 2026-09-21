# Spec Delta

## ADDED Requirements

### Requirement: Published cycles always expose four version slots
JSONB `published_cycles` per team SHALL be `{ versions: { minimal, optimized, maximal, manuel }, latest }` with each version `Cycle | null`. GET `/v1/cycles` and generate/publish `published` MUST always emit the four keys when a team pack exists. A 3-key compute blob MUST coerce to `manuel: null`. An old flat cycle MUST become `versions.optimized` plus `manuel: null`. `latest` MUST be the newest `generated_at`, with ties `manuel` > `maximal` > `optimized` > `minimal`. Bench `EFFORTS` MUST stay `("minimal", "optimized", "maximal")`.

#### Scenario: Three-key blob gains a null manuel slot
- **WHEN** stored salle cycles have only `minimal|optimized|maximal` and the restaurateur GETs `/v1/cycles`
- **THEN** the response pack has `versions.manuel` null and the three compute slots unchanged

#### Scenario: Flat cycle becomes optimized plus null manuel
- **WHEN** stored salle cycles are a flat `{ assignments, … }` blob
- **THEN** GET emits `versions.optimized` as that cycle, `latest` optimized, and `manuel` null

### Requirement: Generate never writes the manuel slot
`POST /v1/generate` with `search_effort: "manuel"` SHALL be HTTP 400 `Champs invalides.` Generate MUST write only `minimal|optimized|maximal`. A later generate MAY take `latest` and MUST leave `versions.manuel` intact.

#### Scenario: Generate manuel is 400
- **WHEN** a company posts generate with `search_effort` manuel
- **THEN** the response is 400 `Champs invalides.` and no slot is written

#### Scenario: Generate after manuel publish keeps the manuel slot
- **WHEN** salle has a published manuel cycle and the restaurateur generates optimized
- **THEN** `versions.manuel` is unchanged and `latest` may become optimized

### Requirement: Live enter can seed an unpublished manuel draft
`POST /v1/live/sandbox/{team}/enter` with `search_effort=manuel` SHALL wrap Core `seed_empty_team_cycle` when the slot is null, then enter, and persist the live sandbox only (`versions.manuel` stays null until publish). A published manuel slot MUST hydrate that slot then enter. A team that is not ready MUST be HTTP 409 `Cette équipe n'est pas prête à calculer.` Preview, commit, and undo MUST stay the existing live routes and MUST NOT rescore.

#### Scenario: Enter manuel without generate
- **WHEN** salle is ready with no published cycle and the restaurateur enters live with `search_effort` manuel
- **THEN** LiveState has empty assignments plus facts, and GET cycles still has `versions.manuel` null (or salle null)

#### Scenario: Enter manuel when the team is not ready
- **WHEN** cuisine is not ready and the restaurateur enters live with `search_effort` manuel
- **THEN** the response is 409 `Cette équipe n'est pas prête à calculer.`

### Requirement: Publish manuel writes the slot without generate logs
Publishing the manuel live draft SHALL write `versions.manuel` with `search_effort: "manuel"` and `generated_at` now (every publish), without `duration_seconds`, without `engine_ref`, without a `generate_logs` row, recompute `latest`, and close the draft. Other slots and the other team MUST stay intact. Discard of a never-published manuel draft SHALL re-seed empty with empty history.

#### Scenario: Publish manuel then GET
- **WHEN** the restaurateur fills, commits, and publishes a never-generated manuel draft
- **THEN** GET cycles has `versions.manuel` with the committed assignments, `latest` manuel, and `generate_logs` count unchanged

#### Scenario: Discard never-published manuel re-seeds empty
- **WHEN** a manuel live draft was never published and the restaurateur discards
- **THEN** LiveState assignments are empty, history is empty, and `versions.manuel` stays null
