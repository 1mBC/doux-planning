## 1. Cycle notes

- [x] 1.1 Add `cycle_score` and `cycle_recap.score` (five notes + weighted global) without changing keep-best, and verify coverage 10, legal 10, exact-contract 10, broken indispo lowers contrat, wellbeing null, roles 10, and `_attempt_key` tuple unchanged

## 2. Guardrails

- [x] 2.1 Run engine / recap / board pytest green without rewriting `saint-cloud.json` and without editing `web/`, `api/`, or `contracts/`

## 3. Chrome notes

- [x] 3.1 Asymmetric hours penalty on `notes.contrat` (over-occupation ×2) and emit `CycleScore.resumes` (five FR keys, null iff the note is null)
- [x] 3.2 Tests: over-occupation hours note strictly lower than the same under-occupation; pile C → 10; `resumes.couverture` contains `postes tenus`; `resumes.contrat` contains `contrat` and/or `indispos tenues`; `generate_cycle` determinism unchanged; engine / recap / board pytest green
