## Why

Coverage holes and wish recap cells still speak in codes or OK / Non tenu only. The restaurateur needs French empty-post clocks, named max-service days, and a visible measure on every wish cell.

## What Changes

- Enrich `evaluate` `empty_post` messages to `{jour} · sem. {A|B|Paire|Impaire} · {service FR} · {début}–{fin} · niveau {n}`.
- Enrich `max_mornings` / `max_middays` / `max_evenings` with French weekdays + max, and `max_coupures` with count + max + week. Severity stays `souhait`.
- Enrich `cycle_recap` wish cell text so the measure is always visible (max services / coupures: `max {limit} · {nA} / {nB} posés`, `OK · ` prefix when held).
- Do not change `contract_hours` severity. Do not rewrite `saint-cloud.json`. No HTTP, no `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: richer `empty_post` / max-service / max-coupure warning text and wish recap measures.

## Impact

- `engine.py` (`empty_post`, `max_*` messages), `context.py` (`_wish_row` texts), optional shared FR helpers in `types.py`. Tests for freeze scenarios. Do not edit `web/`, `api/`, `contracts/`, or the Saint-Cloud snapshot.
