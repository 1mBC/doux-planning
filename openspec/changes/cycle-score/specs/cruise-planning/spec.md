## ADDED Requirements

### Requirement: Cycle score notes out of ten
The system SHALL compute `cycle_score(draft, result)` as five notes 0–10 with one decimal (`couverture`, `legal`, `contrat`, `wellbeing`, `roles`) and a weighted `global`. A missing denominator MUST yield `null` for that note. `global` MUST be the weighted mean of non-null notes with weights couverture 3, legal 3, contrat 2, wellbeing 1.5, roles 0.5, or `null` if every note is null. Coverage MUST be `10 × (required posts − empty_post) / required posts` using the same slice loop as `empty_post`. Legal MUST use non-null `legal_rows` cells only. Contrat MUST average the hours subnote (per fiche with contractual hours > 0) and the indispo subnote (non-null `indispo` cells) when present. Wellbeing MUST be `10 × held / total` from recap wellbeing stats, or null if total is 0. Roles MUST be `10 × (1 − Σ(level − post) / Σ max(0, level − 1))`, or null if the plafond is 0. `cycle_recap` MUST expose the same `CycleScore` as `score`. Keep-best (`_attempt_key`, `SEARCH_*`, `generate_cycle`) MUST stay unchanged.

#### Scenario: Full coverage
- **WHEN** a cycle has required posts and zero `empty_post` warnings
- **THEN** `couverture` is 10.0

#### Scenario: All legal cells held
- **WHEN** every non-null legal recap cell is ok
- **THEN** `legal` is 10.0

#### Scenario: Exact contract hours
- **WHEN** a fiche’s week A and week B hours equal the contractual week
- **THEN** the hours subnote is 10.0

#### Scenario: Broken unavailability
- **WHEN** a posed indispo cell is not ok
- **THEN** the contrat note is lower than the hours-only subnote

#### Scenario: No posed wishes
- **WHEN** wellbeing total is 0
- **THEN** `wellbeing` is null

#### Scenario: Shifts at role level
- **WHEN** every shift `post_level` equals the fiche level
- **THEN** `roles` is 10.0
