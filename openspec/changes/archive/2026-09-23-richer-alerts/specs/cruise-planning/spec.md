## ADDED Requirements

### Requirement: Empty-post warning names the hole
`evaluate` MUST set each `empty_post` `message` to `{jour} · sem. {A|B|Paire|Impaire} · {service FR} · {début}–{fin} · niveau {n}` with French weekday, week label from the draft fiches (`even`/`odd` → Paire/Impaire, otherwise A/B; day 0–6 first label, 7–13 second), French service name (petit-déjeuner / déjeuner / dîner), and `format_clock` hours. `day_index` and `severity` (`couverture`) MUST stay unchanged.

#### Scenario: Morning coverage hole
- **WHEN** a required midday post is empty on Monday of week A
- **THEN** the `empty_post` message contains the French weekday, `sem. A`, the French service, both clocks, and the post level

### Requirement: Max-service and max-coupure warnings name the week
`evaluate` MUST set `max_mornings` / `max_middays` / `max_evenings` `message` to `{name} : {n} {service FR} / max {limit} ({jours} · sem. {…})` where `{jours}` are the French weekdays of that week on which the person has that service. `max_coupures` MUST be `{name} : {n} coupures / max {limit} (sem. {…})`. `day_index` MUST be the week start. Severity MUST stay `souhait`. `contract_hours` severity MUST stay `souhait`.

#### Scenario: Evening cap broken
- **WHEN** a fiche with `max_services.evening` is assigned more evenings than the limit in a week
- **THEN** the `max_evenings` message contains those weekdays and `max {limit}`

### Requirement: Wish recap cells show a measure
`cycle_recap` wish cells MUST always include a measure, not only OK / Non tenu. Max morning / midday / evening and max coupures MUST use `max {limit} · {nA} / {nB} posés`, prefixed with `OK · ` when held. Other posed wish keys MUST keep a visible measure (`indispo` counts or first broken slot; consecutive rest `tenu` or `sem. {…}`; weekend rest day `sam` / `dim` or `sem. {…}`; weekend the French radio value). Contrat text MUST stay `{hA}h · {hB}h / {weekly}h`.

#### Scenario: Broken evening cap on the recap
- **WHEN** a published cuisine cycle has a fiche with `max_services.evening` and week counts that miss the cap
- **THEN** the `max_evening` cell text is `max {limit} · {nA} / {nB} posés` without an OK prefix
