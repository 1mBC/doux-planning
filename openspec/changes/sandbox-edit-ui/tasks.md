## 1. Client sandbox

- [x] 1.1 Add TypeScript types and loaders for enter / GET / preview / commit / undo matching `contracts/http/v1-sandbox-edit.md`, and verify a missing required key throws rather than inventing fields
- [x] 1.2 Add « Mode édition » that `POST /v1/sandbox/enter` then renders grid + warnings from that body (not the example snapshot), hiding example stats/legal/wish tables; verify enter 200 updates the grid and example remains available before enter

## 2. Overlay

- [x] 2.1 Open a French overlay only on occupied début/fin/H cells with the three gestures, then `POST /v1/sandbox/preview` with `{ gesture, shift }` for replace/swap; verify empty cells do not preview and the loader shows until proposals return
- [x] 2.2 List `proposals` in `rank` order and on click `POST /v1/sandbox/commit` with gesture fields, then replace grid + warnings + history from the 200; verify a committed cell matches the new assignment and preview did not mutate the draft beforehand

## 3. History and errors

- [x] 3.1 Show `history` crans and an Annuler control that `POST /v1/sandbox/undo`; verify one undo restores the previous assignments and a 409 shows the French `detail` without changing the grid
- [x] 3.2 Surface FastAPI `detail` for other sandbox errors in French and verify IronBee (or equivalent) flow: enter → overlay preview → commit updates the cell → undo restores

## 4. Overlay feedback (impact + score)

- [x] 4.1 Parse `score` on sandbox state and Proposal `impact` + `current_score` / `trial_score` (no `delta` / `warnings`); retune preview sends `start_minutes` / `end_minutes`; missing keys throw
- [x] 4.2 Hours overlay: début / fin `−` `+` 15 min, one impact (interdits+couverture orange, closer vert, farther/excess rouge), scores as returned, commit those times
- [x] 4.3 Replace / swap: `rank` order, swap title day then time, impact colors, scores before/after; no `delta +/−/=` and no cycle warning dump
- [x] 4.4 Verify ±15 retune, ranked replace, swap with the day, undo (IronBee or curl / Chrome headless)

## 5. Overlay copy (no score list, Valider, contract %)

- [x] 5.1 Remove the overlay score block on retune / replace / swap; keep parsing `score` / `current_score` / `trial_score`
- [x] 5.2 Rename the retune commit control to **Valider** (HTTP commit unchanged)
- [x] 5.3 Append `(before % → after %)` on contract impact lines from `current_hours` / `trial_hours` / `contracted` (French comma; omit if `contracted` is 0)
- [x] 5.4 Verify Valider, no score list, contract % on retune / replace / swap (IronBee or Chrome against the existing Vite)

## 6. Role fit

- [x] 6.1 Type and parse `impact.role_fit` (required key, 0 or 1 `{ current_gap, trial_gap, kind }`); missing key throws
- [x] 6.2 Show `better` green / `worse` red on HoursImpact and SwapReplaceImpact; empty list = no line; « Aucun impact listé » only if nothing including role_fit
- [x] 6.3 Verify replace on a low post: green or red rôle line; same-level candidate has no rôle line

## 7. Fill empty cells

- [x] 7.1 Type `fill` + `FillSlot`; preview `{ gesture: fill, slot, start_minutes, end_minutes }` (null then both numbers); commit `{ fill, slot, employee_id, start, end }`; parse `fill` on history
- [x] 7.2 Empty rest cells in edit mode open a fill overlay (not the three occupied gestures); weekday = monday…sunday; team = person.team; hours from `proposals[0]` only
- [x] 7.3 Fill UI: stepper after first 200, line person + Valider on top, other proposals below with replace-style impact; 409 keeps overlay; history « Créneau posé »
- [x] 7.4 Verify Emma Monday morning fill overlay + structure hours from API, Valider, undo; verify swap `role_fit` green/red on the clicked slot

## 8. History recap and discard

- [x] 8.1 Parse `history[]` recap (`shift`, `slot`, `employee_id`, `start_minutes`, `end_minutes`, `partner`, `impact`; no `current_score` on a cran); map to `HistoryEntry` with a synthetic proposal; missing keys throw
- [x] 8.2 `startEdit` / GET / commit / undo / discard use that list (no React journal as source); Lecture forgets local state and does not discard
- [x] 8.3 **Tout annuler** when `history.length > 0` → `POST /v1/sandbox/discard`; 200 resets grid + empty history; 404 shows French `detail` without changing the grid
- [x] 8.4 Verify: cran → Lecture → Mode édition keeps who / hours / impact; Tout annuler restores the initial draft; example still 92
