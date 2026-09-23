## ADDED Requirements

### Requirement: Live restaurant holds one sandbox per published team cycle
The system SHALL store two independent live sandboxes on a live restaurant, one for salle and one for cuisine. An empty restaurant MUST have neither. Entering a live sandbox when that team has no published cycle MUST fail as no-published-cycle. Re-entering an open live sandbox MUST return the same draft and history. The Saint-Cloud example sandbox MUST remain `state.sandbox`.

#### Scenario: Cuisine without a published cycle cannot enter
- **WHEN** salle has a published cycle and cuisine does not, and the restaurateur enters the cuisine live sandbox
- **THEN** entry fails as no-published-cycle and no cuisine draft is created

### Requirement: Discard and publish a live team sandbox independently
The system SHALL let the restaurateur preview, apply, and undo existing sandbox gestures on a live team draft. Discarding MUST drop only that team’s draft and leave the published cycle intact so a later enter starts from the published assignments with empty history. Publishing MUST write only that team’s published cycle from the current draft assignments and warnings, without calendar-week reconciliation, and MUST leave the other team’s published cycle unchanged.

#### Scenario: Salle cran undo discard restores the published cycle
- **WHEN** salle is generated, the restaurateur enters the salle live sandbox, applies a retune, undoes it, then discards and enters again
- **THEN** the new salle draft assignments match the published salle cycle and history is empty

#### Scenario: Publish updates salle only
- **WHEN** salle has a live sandbox with an applied edit and cuisine has no published cycle, and the restaurateur publishes the salle live sandbox
- **THEN** the salle published cycle matches the draft and cuisine stays unpublished
