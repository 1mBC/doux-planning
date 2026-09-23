# Brief — coller dans le chat **Core Engine**

Le tech lead : recaps d’un cycle publié + warning 11 h avec les deux horloges. Relis `contracts/domain/cycle-recaps.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; master @ **`6c75004`** (`master has weekend-rest landed`). Branche **`recaps/core` depuis `master`**.

Nouveau change OpenSpec **`cycle-recaps`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` weekend-rest-day / wellbeing / generate / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `recaps/core` toi-même**. Message : `feat(core): cycle_recap and rest_between clocks`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. **Ne pas** réécrire `data/examples/saint-cloud.json`.

## Comportement

- `cycle_recap(state, team) -> CycleRecap` (vue sur le publié, pas un 2ᵉ solve). `NoPublishedCycle` si vide.
- `stats` / `legal_*` / `wish_*` selon le freeze. Wish = **nouveau** modèle (pas `we1j` / `weA`).
- `evaluate` : message `rest_between_days` FR avec `{jourA} {fin} → {jourB} {début}`. `day_index` = jour A. Ne pas traduire les autres codes.

## Tests

Scénarios du freeze + pytest domaine / engine / context / board / hydrate verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core recaps pushed @ <sha>`
