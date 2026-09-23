# Spec Delta

## Purpose

The bench and the restaurant each remember one chosen engine. When nothing valid is stored, both use the last engine in the code registry. No version file names a default.

## ADDED Requirements

### Requirement: Bench engine list comes from the registry
The system SHALL expose the bench engine list in registry order. Adding or removing an engine in a later change SHALL change that list without a separate catalogue table. The last name in that list SHALL be the bench fallback engine.

#### Scenario: Picklist matches the registry
- **WHEN** an admin loads either bench page
- **THEN** the engine list is the registry, in registry order, and includes every engine the registry currently exposes

### Requirement: One stored bench engine choice
The system SHALL store at most one bench engine choice for the whole product. Every admin and both bench pages (catalogue and imported) SHALL read and write that same choice. Changing the picklist SHALL store the new name immediately. A bench launch SHALL NOT change the stored choice.

#### Scenario: Choice survives reload
- **WHEN** an admin selects an engine that is in the list and reloads either bench page
- **THEN** that engine is still the selected bench engine

#### Scenario: Both pages share the choice
- **WHEN** an admin selects an engine on Banc IA
- **THEN** Banc Manuels shows the same selected engine

#### Scenario: Launch does not replace the choice
- **WHEN** the stored choice is one engine and a launch request names a different engine that is in the list
- **THEN** that launch uses the named engine and the stored choice stays unchanged

### Requirement: Missing or unknown stored choice uses the last engine
When no bench choice is stored, or the stored name is not in the registry, the system SHALL use the last registry name as the effective bench engine and SHALL store that name. A later read SHALL return that stored name.

#### Scenario: Empty store
- **WHEN** no bench engine choice is stored
- **THEN** the effective bench engine is the last registry name and that name is stored

#### Scenario: Stored name left the registry
- **WHEN** the stored bench engine name is no longer in the registry
- **THEN** the effective bench engine is the last registry name, that name replaces the stored value, and a reload still shows it

### Requirement: Invalid choice is rejected
The system SHALL reject an empty, unknown, or wrongly typed bench engine name on save with HTTP 400 and SHALL leave the previously stored choice unchanged.

#### Scenario: Unknown name
- **WHEN** an admin saves a bench engine name that is not in the registry
- **THEN** the response is HTTP 400 and the stored choice is unchanged

### Requirement: Bench current engine is the effective choice
The versions payload field `engine_ref`, a bench run request with no `engine_ref`, the path compare for the current engine, and the `below_manuel` export SHALL use the effective bench engine. They SHALL NOT read `data/bench/VERSION`.

#### Scenario: Run without an engine name
- **WHEN** an admin launches a bench run without an `engine_ref`
- **THEN** the jobs use the effective bench engine

#### Scenario: Compare and below-manual follow the choice
- **WHEN** the effective bench engine is a name in the registry
- **THEN** path compare and the `below_manuel` export use last-runs of that engine

### Requirement: Gap fill ignores the stored choice
Filling bench gaps SHALL enqueue one job per listed dataset, effort, and registry engine. It SHALL NOT limit itself to the stored bench engine.

#### Scenario: Gaps cover the registry
- **WHEN** an admin fills gaps while a bench engine is stored
- **THEN** missing runs are enqueued for every engine in the registry, not only the stored one

### Requirement: Restaurant engine choice uses the same fallback
The restaurant generate engine SHALL stay a separate stored choice from the bench. The admin picklist SHALL persist it. When that choice is missing or not in the registry, the system SHALL use the last registry name, store it, and use it for restaurant generate. A bench choice SHALL NOT change it.

#### Scenario: Bench choice does not change generate
- **WHEN** an admin selects a bench engine different from the restaurant engine
- **THEN** a restaurant generate still uses the restaurant engine

#### Scenario: Empty restaurant choice
- **WHEN** no restaurant engine is stored
- **THEN** generate uses the last registry name and that name is stored

#### Scenario: Unknown restaurant choice
- **WHEN** the stored restaurant engine is no longer in the registry
- **THEN** generate uses the last registry name, that name replaces the stored value, and the admin picklist shows it after reload

### Requirement: No version file
The system SHALL NOT read or require `data/bench/VERSION`. The last registry name SHALL be the only fallback for both choices.

#### Scenario: File absent
- **WHEN** `data/bench/VERSION` is absent
- **THEN** a bench load and a restaurant generate still resolve to a registry name
