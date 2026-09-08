## Context

See proposal.md. `cycle_recap` already has stats, legal rows, and wish rows. `_overqualification` / `_below_role_count` already exist for keep-best. Coverage empty slots are `empty_post` warnings. Do not change `_attempt_key`.

## Goals / Non-Goals

**Goals:**
- One `cycle_score(draft, result)` used as `cycle_recap.score`.
- Null when a denominator is missing; one-decimal clamp 0–10.

**Non-Goals:**
- Keep-best changes, editable weights, snapshot rewrite, HTTP.

## Decisions

### 1. Score lives next to recap

`cycle_score` builds the same legal / wish / wellbeing tables as `cycle_recap` (shared helper) so legal and indispo notes are recap cells, not a second formula. Coverage counts required slice posts with the same open-day loop as `empty_post`. Roles use `_overqualification` over `Σ max(0, level − 1)` per shift.

### 2. Python field `global_score`

`global` is a keyword. The dataclass stores `global_score`; it is the freeze `global`.

### 3. Keep-best untouched

`_attempt_key` stays a 6-tuple. `SEARCH_*` and `generate_cycle` are not edited.

## Risks / Trade-offs

- [Saint-Cloud hours vs old contrat cell] → Score reads live evaluate + recap, not the frozen wish text. File not rewritten.

## Migration Plan

None. Infra serializes `score` later.

## Open Questions

None.
