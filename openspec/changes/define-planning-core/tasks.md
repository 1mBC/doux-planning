## 1. Domain model

- [ ] 1.1 Scaffold a Python package (3.12) for domain + engine with pytest, and verify `pytest` runs empty-green
- [ ] 1.2 Encode teams, roles with integer levels, and the substitution explanation flag, and verify tests reject an employee whose team does not match their role’s team
- [ ] 1.3 Encode employee profile (name, role, level, team, contractual hours) plus unavailability patterns (weekday, morning/evening, specific service) and the listed wellbeing preferences, and verify round-trip tests cover each pattern
- [ ] 1.4 Encode service mode (continuous vs named services), closures, arrival/departure waves on a 15-minute grid, and weekday applicability, and verify a wave time not aligned to 15 minutes is rejected
- [ ] 1.5 Encode the six default legal rules as displayable data, and verify they are present and readable without generation
- [ ] 1.6 Encode invite-code generation and restaurant-account linking, and verify a valid code attaches an employee account and an invalid code does not

## 2. Coverage and post matching

- [ ] 2.1 Derive 15-minute coverage slices from arrival and departure waves (posts required and posts that must remain), and verify the kitchen midday example (10:00 L4, 11:00 two L2, 11:30 L1, then departures) produces the expected slice map
- [ ] 2.2 Implement exclusive-post matching with nearest-level descent and frozen role per shift, and verify the two-chefs / one-sous-chef / one-commis / no-plongeur scenario matches the spec (plongeur empty, sole-chef never sent to plonge)
- [ ] 2.3 Emit couverture warnings for empty posts, and verify unfilled posts remain empty (no extra filling)

## 3. Scoring and warnings

- [ ] 3.1 Score interdit rules (11h rest including cycle wrap, two rest days per week, 5h max coupure, 11h cuisine / 11.5h salle daily, 48h weekly, stated unavailability) and verify each rule produces an interdit warning in a fixture
- [ ] 3.2 Score souhait rules (wellbeing list + contractual hours miss/excess) and verify consecutive rest days and under-scheduled hours produce souhait warnings only
- [ ] 3.3 Attach warnings to a draft without blocking, and verify a draft with an acknowledged interdit warning can still be marked publishable

## 4. Engine API

- [ ] 4.1 Expose one engine entry for evaluate(draft) → assignments + warnings, and verify generate, add-candidate ranking, and swap all call it (no second scorer)
- [ ] 4.2 Implement candidate ranking for an empty slot (eligible first, then opportunity / warning cost), and verify the list order and per-candidate warnings
- [ ] 4.3 Implement swap as dual reassignment through the same engine, and verify rest and coverage warnings match a manual remove+add of both people
- [ ] 4.4 Generate a 14-day cycle in one solve (wave templates, not per-slice variables), including wrap-around rest and every-other-weekend preference, and verify sequential week-A-then-week-B is not used and a both-weekends-worked result is a souhait warning

## 5. Cycle, instances, sandbox

- [ ] 5.1 Persist published cycle vs calendar instance (cycle reference + intents + grid), and verify a clean future week follows the cycle and elapsed days are not rewritten
- [ ] 5.2 Record unavailability and forced-assignment intents on publish from a week sandbox, and verify the week stores intents in addition to the grid
- [ ] 5.3 Implement sandbox state: one per restaurant, target chosen at entry (`cycle` or `week-id`) immutable, persist across leave/return, live rescore after each edit, discard vs publish, and verify a week-target publish does not mutate the cycle
- [ ] 5.4 Route structural config edits (waves, closures, service mode, weekday mapping) through the cycle sandbox only, and verify “open earlier on Tuesday” published on the cycle updates clean future Tuesdays
- [ ] 5.5 On cycle publish, auto-apply clean weeks and, for each dirty week, compute `new cycle + intents` then require accept / keep / open-in-sandbox, and verify week 12 with “Karim absent Tuesday” is not overwritten until that choice
- [ ] 5.6 Hide sandbox drafts from employee-facing reads, and verify employees only receive the last published planning (own shifts until the visibility question is decided)

## 6. Onboarding helpers

- [ ] 6.1 Provide at least one editable service-structure template (e.g. service-based brasserie), and verify applying it pre-fills waves that remain editable
