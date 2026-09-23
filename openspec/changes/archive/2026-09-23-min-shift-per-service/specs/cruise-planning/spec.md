# Spec Delta

## ADDED Requirements

### Requirement: Sandbox fill and retune use per-service minimum
Sandbox preview of retune or fill MUST reject a duration shorter than that employee’s minimum for the slot’s service. Fill MUST also skip other candidates whose minimum for that service is longer than the proposed window. The default when the service key is absent is 4 hours.

#### Scenario: Retune below the service minimum is rejected
- **WHEN** the restaurateur previews a retune shorter than that person’s minimum for the shift’s service
- **THEN** the preview fails as below minimum shift hours

#### Scenario: Fill uses the slot’s service minimum
- **WHEN** the restaurateur previews a fill on evening for a person whose evening minimum is 3 hours and midday is unset
- **THEN** a 3-hour evening window is accepted and a 3-hour midday window is still below that person’s midday minimum
