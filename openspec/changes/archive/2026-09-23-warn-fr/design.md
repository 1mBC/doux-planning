## Context

See proposal.md. `evaluate` already emits these codes with English `message` text. `empty_post` / max-service / `rest_between_days` already use `WEEKDAY_FR`, `SERVICE_FR`, `week_label_for_day`, and `format_clock`. Recap cells already show French measures and must not change.

## Goals / Non-Goals

**Goals:**
- French `message` for the twelve remaining codes, using the same hour / day / week helpers as the richer-alerts slice.

**Non-Goals:**
- Changing severities, codes, `day_index`, recap cells, or already-French messages.
- Rewriting `saint-cloud.json` (frozen English snapshot stays until a later file).

## Decisions

### 1. Message strings only in `evaluate`

Keep emission sites. Swap the format string. Reuse `_draft_week_scheme` / `week_label_for_day` / `SERVICE_FR` / `WEEKDAY_FR`. Add `hours_label` next to `format_clock` (same shape as context `_hours_label`) so engine does not import `context`.

### 2. Recap and snapshot stay put

`_wish_row` / `_legal_row` already format their own cells. Do not edit `context.py`. Do not rewrite the public example file.

## Risks / Trade-offs

- [Preview tests construct English `Warning` literals] → Those are identity fixtures, not `evaluate` output; leave them.
- [Saint-Cloud file still has English messages] → Accepted this slice; hydrate reads the snapshot.

## Migration Plan

None. Snapshot refresh is a later file.

## Open Questions

None.
