## Why

`empty_post`, max-service, max-coupure, and 11 h warnings already speak French. The remaining `evaluate` messages are still English, so the restaurateur sees a mixed language list.

## What Changes

- Translate the remaining `evaluate` `message` texts to the freeze French forms: `contract_hours`, `consecutive_rest_days`, `weekend_rest_day`, `weekend_every_two_weeks`, `weekend_even_weeks`, `weekend_odd_weeks`, `unavailability`, `max_daily_hours`, `max_coupure`, `weekly_rest_days`, `max_weekly_hours`, `assigned_on_closure`.
- Leave `severity`, `code`, and `day_index` unchanged. `contract_hours` stays `souhait`.
- Do not retouch already-French messages (`empty_post`, max services / coupures, `rest_between_days`). Do not change recap cells. Do not rewrite `saint-cloud.json`. No HTTP, no `web/` / `api/` / `contracts/` edits.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `cruise-planning`: remaining `evaluate` warning messages in French.

## Impact

- `engine.py` warning `message` strings only. Tests assert a French substring per freeze code. Do not edit `web/`, `api/`, `contracts/`, recap cell builders, or the Saint-Cloud snapshot.
