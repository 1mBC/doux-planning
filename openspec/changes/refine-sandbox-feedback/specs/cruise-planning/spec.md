## ADDED Requirements

### Requirement: Preview proposals carry impact and scores without mutating the draft
A sandbox preview MUST leave assignments, last scored result, and history unchanged. Each returned proposal MUST include the local impact summary (including `role_fit` when the clicked slot’s downrole points change) and the keep-best planning keys for current vs trial so an overlay can show before → after without reading unchanged cycle warnings.

#### Scenario: Retune preview leaves the draft untouched
- **WHEN** the restaurateur previews a single-step retune
- **THEN** sandbox assignments, last result, and history length are the same as before the preview

#### Scenario: Fill preview leaves the draft untouched
- **WHEN** the restaurateur previews filling an empty cell
- **THEN** sandbox assignments, last result, and history length are the same as before the preview
