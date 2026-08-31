## 1. Domain model

- [x] 1.1 Scaffold a Python package (3.12) for domain + engine with pytest, and verify `pytest` runs empty-green
- [x] 1.2 Encode teams, roles with integer levels, and the substitution explanation flag, and verify tests reject an employee whose team does not match their role’s team
- [x] 1.3 Encode employee profile (name, role, level, team, contractual hours) plus unavailability patterns (weekday, morning/evening, specific service) and the listed wellbeing preferences, and verify round-trip tests cover each pattern
- [x] 1.4 Encode service mode (continuous vs named services), closures, arrival/departure waves on a 15-minute grid, and weekday applicability, and verify a wave time not aligned to 15 minutes is rejected
- [x] 1.5 Encode the six default legal rules as displayable data, and verify they are present and readable without generation
- [x] 1.6 Encode invite-code generation and restaurant-account linking, and verify a valid code attaches an employee account and an invalid code does not

## 2. Coverage and post matching

- [x] 2.1 Derive 15-minute coverage slices from arrival and departure waves (posts required and posts that must remain), and verify the kitchen midday example (10:00 L4, 11:00 two L2, 11:30 L1, then departures) produces the expected slice map
- [x] 2.2 Implement exclusive-post matching with nearest-level descent and frozen role per shift, and verify the two-chefs / one-sous-chef / one-commis / no-plongeur scenario matches the spec (plongeur empty, sole-chef never sent to plonge)
- [x] 2.3 Emit couverture warnings for empty posts, and verify unfilled posts remain empty (no extra filling)

## 3. Scoring and warnings

- [x] 3.1 Score interdit rules (11h rest including cycle wrap, two rest days per week, 5h max coupure, 11h cuisine / 11.5h salle daily, 48h weekly, stated unavailability) and verify each rule produces an interdit warning in a fixture
- [x] 3.2 Score souhait rules (wellbeing list + contractual hours miss/excess) and verify consecutive rest days and under-scheduled hours produce souhait warnings only
- [x] 3.3 Attach warnings to a draft without blocking, and verify a draft with an acknowledged interdit warning can still be marked publishable

## 4. Engine API

- [x] 4.1 Expose one engine entry for evaluate(draft) → assignments + warnings, and verify generate, add-candidate ranking, and swap all call it (no second scorer)
- [x] 4.2 Implement candidate ranking for an empty slot (eligible first, then opportunity / warning cost), and verify the list order and per-candidate warnings
- [x] 4.3 Implement swap as dual reassignment through the same engine, and verify rest and coverage warnings match a manual remove+add of both people
- [x] 4.4 Generate a 14-day cycle in one solve (wave templates, not per-slice variables), including wrap-around rest and every-other-weekend preference, and verify sequential week-A-then-week-B is not used and a both-weekends-worked result is a souhait warning
- [x] 4.5 Skip unavailable employees at generation fill time and verify a Monday-unavailable person is not assigned any Monday shift
- [x] 4.6 Skip service-level unavailability at generation and verify weekday-midday-unavailable staff can still be assigned weekday evening
- [x] 4.7 When hours-to-contract ratios are equal, prefer exact level and verify a level-3 post goes to a level-3 employee rather than a level-4 colleague at the same ratio
- [x] 4.8 Assign a higher level when the closer level is overloaded on contract hours and verify a level-3 post goes to a level-4 employee once the eligible level-3 is at or above hours
- [x] 4.9 Assign a level-3 when the eligible level-2 is overloaded on contract hours and verify a level-2 post goes to the level-3 employee
- [x] 4.10 Do not assign over contractual hours while a teammate is under hours and verify a 15-hour employee is not given a further shift once at 15h if a 35-hour colleague is still under
- [x] 4.11 Keep enough people working to cover posts when planning rest and verify that when four midday posts need four eligible people, none of those four is rested that day and the posts fill
- [x] 4.12 Place consecutive rest on weekday pairs only (not Saturday–Sunday) and verify staff with that preference still work Saturday when Sunday is closed
- [x] 4.13 Do not assign the only person who can cover an earlier empty post to a later post when another colleague can take the later post, and verify a 10:00 level-1 opening is filled rather than leaving it empty while that person sits on a 12:00 level-2
- [x] 4.14 When hours-to-contract ratios are equal, prefer completing a started day over opening a new person, and verify an evening post goes to the midday person rather than a colleague still off that day
- [x] 4.15 Search several deterministic generation starts (rest seed, staff order, start day) plus a same-day reassignment repair, keep the best, and verify a midi-then-evening hole is filled by moving the midday person and giving midi to a midi-only colleague
- [x] 4.16 Count wellbeing coupures per week (not per cycle) and verify three split days in week A produce a souhait on week A only when the cap is two per week

## 5. Cycle, instances, sandbox

- [x] 5.1 Persist published cycle vs calendar instance (cycle reference + intents + grid), and verify a clean future week follows the cycle and elapsed days are not rewritten
- [x] 5.2 Record unavailability and forced-assignment intents on publish from a week sandbox, and verify the week stores intents in addition to the grid
- [x] 5.3 Implement sandbox state: one per restaurant, target chosen at entry (`cycle` or `week-id`) immutable, persist across leave/return, live rescore after each edit, discard vs publish, and verify a week-target publish does not mutate the cycle
- [x] 5.4 Route structural config edits (waves, closures, service mode, weekday mapping) through the cycle sandbox only, and verify “open earlier on Tuesday” published on the cycle updates clean future Tuesdays
- [x] 5.5 On cycle publish, auto-apply clean weeks and, for each dirty week, compute `new cycle + intents` then require accept / keep / open-in-sandbox, and verify week 12 with “Karim absent Tuesday” is not overwritten until that choice
- [x] 5.6 Hide sandbox drafts from employee-facing reads, and verify employees only receive the last published planning (own shifts until the visibility question is decided)

## 6. Onboarding helpers

- [x] 6.1 Provide at least one editable service-structure template (e.g. service-based brasserie), and verify applying it pre-fills waves that remain editable
