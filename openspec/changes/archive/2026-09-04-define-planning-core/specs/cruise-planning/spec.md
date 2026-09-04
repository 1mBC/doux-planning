## Purpose

Gère le planning de croisière : un cycle répétable de 14 jours, des instances calendaires, des exceptions comme intents, et un bac à sable à une seule cible avant toute publication.

## ADDED Requirements

### Requirement: Fourteen-day repeating cycle
The system SHALL treat the cruise planning as a 14-day cycle (week A and week B) that repeats. Constraints that wrap from the last day of week B to the first day of week A (including legal rest) MUST be enforced on the cycle.

#### Scenario: Cycle wrap rest
- **WHEN** an employee finishes late on week-B Sunday
- **THEN** the cycle is invalid without sufficient rest before week-A Monday, and the engine reports an interdit-level warning

### Requirement: Calendar instances copy the cycle
The system SHALL instantiate the published cycle onto calendar weeks. A week with no intents follows the cycle. The past MUST NOT be rewritten when a new cycle is published.

#### Scenario: Clean future week follows cycle
- **WHEN** a new cycle is published and next week has no intents
- **THEN** next week’s published grid matches the new cycle for those weekdays

#### Scenario: Past unchanged
- **WHEN** a new cycle is published
- **THEN** already-elapsed days keep their previously published assignments

### Requirement: Exceptions are intents
The system SHALL store a dirty week as: cycle reference + list of intents + published grid. Intents are restaurateur-stated constraints or forced assignments (for example absence, forced person on a slot), not only cell diffs.

#### Scenario: Absence is an intent
- **WHEN** the restaurateur marks Karim unavailable next Tuesday in a week sandbox and publishes
- **THEN** that week stores an unavailability intent for Karim on Tuesday in addition to the resulting grid

### Requirement: Sandbox has a single target chosen at entry
The system SHALL require the restaurateur to choose the sandbox target when entering: either the cruise cycle or one calendar week. That target MUST NOT change during the session or at publish time.

#### Scenario: Enter on a week
- **WHEN** the restaurateur opens the sandbox for calendar week 12
- **THEN** all edits in that session apply only to week 12 and publish writes week 12, not the cycle

### Requirement: Structural config uses the cycle sandbox
Changes that alter coverage needs (service mode, closures, arrival/departure waves, which days a structure applies to) MUST be made in a cycle-target sandbox, then published like any other cycle edit.

#### Scenario: Open earlier on Tuesdays
- **WHEN** the restaurateur changes Tuesday cuisine arrival waves in a cycle sandbox and publishes
- **THEN** the published cycle uses the new Tuesday waves and clean future Tuesdays follow them

### Requirement: Sandbox chains edits then publishes or discards
The system SHALL allow multiple edits in one sandbox (including regeneration) with live warnings after each edit. Publish commits the whole draft to the chosen target. Discard throws the draft away. The system MUST keep at most one sandbox per restaurant and MUST persist it if the restaurateur leaves the screen.

#### Scenario: Chain then publish
- **WHEN** the restaurateur adds a person, then swaps two slots, then publishes
- **THEN** both edits appear together on the published target and employees see only the published result

#### Scenario: Leave and return
- **WHEN** the restaurateur leaves with an unpublished sandbox
- **THEN** returning restores the same draft and target

### Requirement: Dirty weeks get a reconciliation proposal
When a cycle is published, weeks that already have intents MUST NOT be silently overwritten. For each such week the system SHALL compute a new proposal by solving the new cycle plus that week’s intents, then ask the restaurateur to accept the proposal, keep the current week, or open that week in a sandbox.

#### Scenario: Reconcile a week with an absence
- **WHEN** the restaurateur publishes a new cycle and week 12 has a “Karim absent Tuesday” intent
- **THEN** the system presents a week-12 proposal that applies the new cycle and keeps Karim off Tuesday, and does not replace week 12 until the restaurateur accepts, keeps, or further edits it

### Requirement: Employees see only published planning
The system SHALL expose to linked employees only published cycle/instances, never sandbox drafts.

#### Scenario: Draft is invisible
- **WHEN** a cycle sandbox contains unpublished swaps
- **THEN** employees viewing the planning still see the last published version
