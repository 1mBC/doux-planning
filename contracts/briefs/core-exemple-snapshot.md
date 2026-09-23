# Brief — coller dans le chat **Core Engine**

Le tech lead : **file warn-fr close** (`master has warn-fr landed` Core @ `09855b0`, Infra merge @ `3e910dc`). On réécrit le snapshot public pour que `/exemple` parle FR + wish live. Relis `contracts/domain/exemple-snapshot.md` (tu le suis, tu ne le modifies pas).

`git pull origin master` (plus récent que `3e910dc`, doit contenir ce brief) ; branche **`snapshot/core` depuis `master`**.

Nouveau change OpenSpec **`exemple-snapshot`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` warn-fr / cycle-recaps / seed / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `snapshot/core` toi-même**. Message : `feat(core): refresh saint-cloud snapshot recap`. Pas de PR master. Signal le SHA **et** `warnings.length` + `wellbeing.held/total`.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de `generate_cycle`. `restaurant` + `assignments` + `search_effort` / `calendars` / `seconds` **inchangés**.

## Comportement

`evaluate` + `cycle_recap` salle sur le draft du fichier → réécrire `planning.warnings` / `stats` / `legal_rows` / `wish_cols` / `wish_rows`. Plus de `we1j` / `weA`. Messages FR. 92 shifts, Théo 11h–16h, Diane `30h · 29h / 39h` gardés.

## Tests

Scénarios du freeze + hydrate / seed / domaine verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core snapshot pushed @ <sha>, warnings=<n>, wellbeing=<held>/<total>`
