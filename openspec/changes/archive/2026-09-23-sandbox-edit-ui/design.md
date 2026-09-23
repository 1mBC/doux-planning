## Context

See `proposal.md`. HTTP freeze: `contracts/http/v1-sandbox-edit.md`. Example screen stays `contracts/http/v1-examples.md`. Engine previews already exist; React must not call generate or rank, and must not recompute `score` / `impact`.

```
lecture          GET /v1/examples/saint-cloud
                      |
Mode édition --> POST /v1/sandbox/enter
                      |
grille+warnings  GET /v1/sandbox | commit | undo | discard   (+ score du draft)
                 history[] recap (qui / heures / impact)
                      |
overlay heures   POST /v1/sandbox/preview  { retune, shift, start, end }
                 200 { proposals: [ Proposal ] }   (0 ou 1)
overlay replace  POST /v1/sandbox/preview  { replace|swap, shift }
  / swap         200 { proposals: [ … ] }  tri rank
overlay fill     POST /v1/sandbox/preview  { fill, slot, start, end | null }
                 200 { proposals: [ … ] }  rang 1 = ligne si possible
                 POST /v1/sandbox/commit   --> état + recap
                 POST /v1/sandbox/undo     --> état | 409
                 POST /v1/sandbox/discard  --> brouillon initial, history []
```

## Goals / Non-Goals

**Goals:**
- Overlay on occupied slots; retune via ±15 then one trial; replace/swap in engine `rank` order; fill overlay on empty cells; commit replaces draft; undo last cran; discard resets the draft.
- History who / hours / impact come from the API recap (not a React journal). Lecture may drop local state.
- Overlay shows `impact` only (no score block). Hours for fill come from the preview body, never invented. French chrome; FastAPI `detail` shown as-is.

**Non-Goals:**
- Auth, week vs cycle, publish, jobs, websockets, scoring in the client.
- Listing `delta` or the full cycle `warnings` on a proposal.
- Hardcoding structure hours (e.g. 10h). Generating a new cycle, CORS unless the Vite proxy fails.

## Decisions

### 1. Hide example recap tables in edit mode

Sandbox planning has no `stats` / `legal_rows` / `wish_rows`. Hide those example tables while editing so they cannot be mistaken for the draft. The example screen still shows them when not editing. Draft `score` from the sandbox body may be shown as-is (six champs moteur), never recomputed.

### 2. Shift identity without duration_hours on write

Send the contract identity fields. Keep `duration_hours` on read for the grid Total column (sum of displayed hours, as today). `partner` includes `day_index` and `weekday`.

### 3. Overlay is a modal, not a route

No extra HTTP. Close overlay on escape / cancel without commit. Preview only after a gesture is chosen. Retune does **not** preview on gesture click (identity would 400) — preview after each ±15.

### 4. Gesture labels and overlay rows

`retune` → Changer les heures / Ajustement d’heures  
`replace` → Attribuer une autre personne / Remplacement  
`swap` → Échanger / Échange  

**Heures:** stepper début / fin (±15). Un `impact` : `new_interdits` + `coverage_added` orange ; contrat `closer` vert « gagné N min » (`(trial_hours - current_hours)` en minutes) ; `farther` / `excess` rouge ; `role_fit` comme ci-dessous (souvent vide). Pas d’inchangé. Pas de liste `current_score` / `trial_score`. Bouton **Valider** (commit HTTP inchangé).

**Replace / swap:** titre replace = nom ; titre swap = **jour puis heure** (`weekday` / `day_index` + clock). Par ligne : interdits rouge, souhaits cassés orange, contrat des deux personnes (vert `closer` / jaune sinon), `role_fit` du **créneau cliqué** (vert `better` / rouge `worse`). Ne pas trier. Pas de `delta +/−/=`. Pas de bloc score.

**Fill (case vide) :** pas les 3 gestes. `slot` = `employee_id`, `day_index`, `weekday` (`monday`…`sunday` via `day_index % 7`, jamais « Lundi »), `service_id`, `team` = `person.team`. Ouverture : `start_minutes` / `end_minutes` null. Après 200, curseur sur `proposals[0]` start/end ; chaque pas renvoie les deux nombres. Haut = personne de la ligne si présente + impact + Valider ; dessous = autres `rank`. Commit heures du preview. 409 : overlay ouvert.

**Contrat % (affichage) :** sur chaque ligne horaire / contrat, `(current_hours / contracted * 100 → trial_hours / contracted * 100)`, virgule française. Omettre les parenthèses si `contracted` = 0. Ce n’est pas un score moteur.

**Rôle (`role_fit`) :** 0 ou 1 entrée. `better` → vert « poste plus proche du niveau (−N) » avec `N = current_gap - trial_gap`. `worse` → rouge « surqualification +N » avec `N = trial_gap - current_gap`. Liste vide = pas de ligne. N lu sur les champs, pas recalculé depuis niveau/poste.

### 5. History recap is the source of truth

`history[]` is no longer `{ index, gesture }` only. Each cran has `shift` | `slot`, `employee_id`, `start_minutes`, `end_minutes`, `partner`, `impact` (no `current_score` — normal). The client maps that recap to `HistoryEntry` (synthetic proposal for impact display; dummy scores OK because scores are not shown). `startEdit`, GET, commit, undo, and discard replace the list from the body. No React journal as source. **Lecture** only leaves edit mode; it MUST NOT `discard`.

**Tout annuler** is shown when `history.length > 0`. It `POST /v1/sandbox/discard`. 200 replaces grid + empty history (hydrated cycle draft). 404 shows French `detail` and MUST NOT change the grid. Example snapshot (92 %) is untouched.

### 6. API errors

Parse FastAPI `detail` (string). Identity retune / durée < min → 400, shown in the overlay, draft unchanged. 409 undo: banner, draft unchanged. 404 discard: banner, draft unchanged. Missing contract keys: stop, French error, do not invent.

### 7. Vite proxy unchanged

`/v1` → `http://127.0.0.1:8000`. No new routes. No `api/` change unless proxy cannot reach the sandbox.

## Risks / Trade-offs

- [Preview slow] → Loader in the overlay; no fake proposals.
- [Stale overlay after commit] → Close overlay and bind clicks to the new assignments.
- [Click vs sticky name column] → Occupied: only start/end/H of a filled slot. Empty: the three rest cells of that day/service.
- [Retune identity 400] → Do not preview until the restaurateur steps ±15.
- [Fill hours] → Never default to 10h; wait for `proposals[0]` after the first preview.

## Migration Plan

Additive UI. Rollback = revert `web/` sandbox files. Example JSON untouched.

## Open Questions

None that block this slice.
