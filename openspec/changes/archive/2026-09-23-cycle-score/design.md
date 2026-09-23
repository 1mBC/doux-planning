## Context

See proposal.md. `cycle_recap` already has stats, legal rows, and wish rows. `_overqualification` / `_below_role_count` already exist for keep-best. Coverage empty slots are `empty_post` warnings. Do not change `_attempt_key`. Freeze: `contracts/domain/score.md` (follow, do not edit).

## Goals / Non-Goals

**Goals:**
- One `cycle_score(draft, result)` used as `cycle_recap.score`.
- Null when a denominator is missing; one-decimal clamp 0–10.
- Asymmetric hours penalty (over-occupation ×2 vs under-occupation).
- Five French `resumes` strings, `null` iff the matching note is `null`.

**Non-Goals:**
- Keep-best changes, editable weights, snapshot rewrite, HTTP, UI chrome.

## Decisions

### 1. Score lives next to recap

`cycle_score` builds the same legal / wish / wellbeing tables as `cycle_recap` (shared helper) so legal and indispo notes are recap cells, not a second formula. Coverage counts required slice posts with the same open-day loop as `empty_post`. Roles use `_overqualification` over `Σ max(0, level − 1)` per shift.

### 2. Python field `global_score`

`global` is a keyword. The dataclass stores `global_score`; it is the freeze `global`. `resumes` has no `global` key.

### 3. Hours penalty is asymmetric

Per fiche with `C > 0`, week hours `h` (same source as recap / `contract_hours`):

```
pen(h, C) = (C − h) / C           if h ≤ C
          = 2 × (h − C) / C       if h > C
pen_i     = pen(h_sem_A, C) + pen(h_sem_B, C)
note_i    = 10 × max(0, 1 − pen_i / 2)
```

`notes.contrat` averages hours and indispo subnotes when present.

### 4. `ScoreResumes` next to `ScoreNotes`

Same five keys. Forms from freeze (`postes tenus`, `règles tenues`, `{h_posées} occupées / {h_contrat} contrat` via `_hours_label`, `indispos tenues` on the next line if hours are present, `souhaits tenus`, `{N} affectés · {k} poste en sous-rôle / {N}` with `N = stats.assignments` and `k = stats.below_role`). Contrat parts joined by `\n`, not ` · `. The roles resume is not the note formula (écart / plafond).

### 5. Keep-best untouched

`_attempt_key` stays a 6-tuple. `SEARCH_*` and `generate_cycle` are not edited.

## Risks / Trade-offs

- [Saint-Cloud hours vs old contrat cell] → Score reads live evaluate + recap, not the frozen wish text. File not rewritten.

## Migration Plan

None. Infra serializes `score` (including `resumes`) later.

## Open Questions

None.
