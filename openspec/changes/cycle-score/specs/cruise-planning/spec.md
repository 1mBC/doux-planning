## ADDED Requirements

### Requirement: Cycle score notes out of ten
The system SHALL compute `cycle_score(draft, result)` as five notes 0–10 with one decimal (`couverture`, `legal`, `contrat`, `wellbeing`, `roles`) and a weighted `global`. A missing denominator MUST yield `null` for that note. `global` MUST be the weighted mean of non-null notes with weights couverture 3, legal 3, contrat 2, wellbeing 1.5, roles 0.5, or `null` if every note is null. Coverage MUST be `10 × (required posts − empty_post) / required posts` using the same slice loop as `empty_post`. Legal MUST use non-null `legal_rows` cells only. Contrat MUST average the hours subnote (per fiche with contractual hours > 0) and the indispo subnote (non-null `indispo` cells) when present; both missing MUST yield `contrat` null. Hours MUST use `pen(h, C) = (C − h) / C` when `h ≤ C` and `2 × (h − C) / C` when `h > C`, `pen_i` the sum of both weeks, `note_i = 10 × max(0, 1 − pen_i / 2)`, then the mean of `note_i`. Wellbeing MUST be `10 × held / total` from recap wellbeing stats, or null if total is 0. Roles MUST be `10 × (1 − Σ(level − post) / Σ max(0, level − 1))`, or null if the plafond is 0. `cycle_recap` MUST expose the same `CycleScore` as `score`. Keep-best (`_attempt_key`, `SEARCH_*`, `generate_cycle`) MUST stay unchanged. The JSON key `contrat` MUST stay `contrat`.

#### Scenario: Full coverage
- **WHEN** a cycle has required posts and zero `empty_post` warnings
- **THEN** `couverture` is 10.0

#### Scenario: All legal cells held
- **WHEN** every non-null legal recap cell is ok
- **THEN** `legal` is 10.0

#### Scenario: Exact contract hours
- **WHEN** a fiche’s week A and week B hours equal the contractual week
- **THEN** the hours subnote is 10.0

#### Scenario: Over-occupation vs under-occupation
- **WHEN** two fiches have the same `|h − C|` per week and one is over C while the other is under C
- **THEN** the over-occupation hours subnote is strictly lower than the under-occupation hours subnote

#### Scenario: Broken unavailability
- **WHEN** a posed indispo cell is not ok
- **THEN** the contrat note is lower than the hours-only subnote

#### Scenario: No posed wishes
- **WHEN** wellbeing total is 0
- **THEN** `wellbeing` is null

#### Scenario: Shifts at role level
- **WHEN** every shift `post_level` equals the fiche level
- **THEN** `roles` is 10.0

### Requirement: Cycle score French resumes
The system SHALL emit `CycleScore.resumes` with the same five keys as `notes`. Each resume MUST be `null` if and only if the matching note is `null`. Forms MUST be: couverture `{tenus} / {requis} postes tenus`; legal `{ok} / {n} règles tenues`; contrat present parts joined by ` · ` (`{h_posées} / {h_contrat} contrat` with `_hours_label` on `stats.hours.assigned` and `stats.hours.contracted`, and/or `{ok} / {n} indispos tenues`); wellbeing `{held} / {total} souhaits tenus`; roles `écart {ecarts} / {plafond}`. There MUST be no `resumes.global`.

#### Scenario: Coverage resume names held posts
- **WHEN** `notes.couverture` is not null
- **THEN** `resumes.couverture` contains `postes tenus`

#### Scenario: Occupation resume names present parts
- **WHEN** `notes.contrat` is not null
- **THEN** `resumes.contrat` contains `contrat` and/or `indispos tenues` according to which subnotes are present
