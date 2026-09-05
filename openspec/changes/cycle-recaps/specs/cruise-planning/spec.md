## ADDED Requirements

### Requirement: Cycle recap reads the published result
`cycle_recap(state, team)` SHALL return stats, legal columns/rows, and wish columns/rows for that team’s published cycle without calling `generate_cycle`. Missing published cycle MUST raise `NoPublishedCycle`. Wish columns MUST use the current wellbeing model keys (`contrat`, `indispo`, `consecutive_rest`, `weekend_rest_day`, `weekend`, `max_morning` / `max_midday` / `max_evening`, `max_coupures`) and MUST NOT use `we1j`, `weA`, `weB`, `soirs`, or `repos2`. Salle legal columns MUST omit `max_daily_cuisine`; cuisine MUST omit `max_daily_salle`. `stats.assignments` MUST equal the number of published assignments. A posed `weekend_rest_day` on any team fiche MUST add that wish column; a fiche without the box MUST have a null cell.

#### Scenario: Generated salle recap
- **WHEN** a salle-ready restaurant has a minimal published salle cycle
- **THEN** `cycle_recap` has one legal row per salle fiche, no `max_daily_cuisine` column, and `stats.assignments` equals the assignment count

#### Scenario: Weekend rest day column
- **WHEN** one salle fiche has `weekend_rest_day` and a colleague does not
- **THEN** `wish_cols` includes `weekend_rest_day` and the colleague’s cell is null

#### Scenario: No dead snapshot wish keys
- **WHEN** a live recap is built
- **THEN** `wish_cols` keys do not include `we1j` or `weA`

### Requirement: Rest-between warning shows both clocks
`evaluate` MUST set `rest_between_days` `message` to `{name} : moins de 11 h de repos ({jourA} {fin} → {jourB} {début})` with French weekday names and `formatClock` hours. `day_index` MUST be day A. Other warning codes MUST keep their existing messages.

#### Scenario: Short overnight rest
- **WHEN** two consecutive-day shifts leave fewer than 11 h between the last end and the next start
- **THEN** the warning message contains both French days and both clocks
