# Brief — coller dans le chat **Core Engine**

Le tech lead : messages d’alerte + cellules souhaits **plus parlants**. Relis `contracts/domain/cycle-recaps.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; master @ **`f5aa402`** (`master has recaps landed`). Branche **`alerts/core` depuis `master`**.

Nouveau change OpenSpec **`richer-alerts`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` cycle-recaps / weekend-rest / wellbeing / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `alerts/core` toi-même**. Message : `feat(core): richer empty_post and wish recap text`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. **Ne pas** réécrire `saint-cloud.json`. `contract_hours` **reste** `severity: souhait`.

## Comportement

- `empty_post` : FR `{jour} · sem. … · {service} · {début}–{fin} · niveau {n}`.
- `max_mornings` / `_middays` / `_evenings` : FR avec jours de la semaine + max. `max_coupures` : compte + max + sem.
- `cycle_recap` wish : mesure toujours visible. Max services / coupures = `max {limit} · {nA} / {nB} posés` (`OK · ` si tenu).

## Tests

Scénarios du freeze (empty_post + max evening + cellule wish) + pytest domaine / engine / recap / board / hydrate verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core alerts pushed @ <sha>`
