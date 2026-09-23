# Brief — coller dans le chat **Core Engine**

Le tech lead : **file alerts close** (`master has alerts landed` @ `f5e2e673cc5e33a15c14217530dc820792022d89`, UI v0.16.0). Il reste les `evaluate.message` encore **anglais**. Relis `contracts/domain/cycle-recaps.md` section **Warnings restants FR** (tu le suis, tu ne le modifies pas).

`git pull origin master` (plus récent que `f5e2e67`, doit contenir ce brief). Branche **`warn-fr/core` depuis `master`**.

Nouveau change OpenSpec **`warn-fr`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` richer-alerts / cycle-recaps / weekend-rest / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `warn-fr/core` toi-même**. Message : `feat(core): remaining evaluate messages in French`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. **Ne pas** réécrire `saint-cloud.json`. `severity` / `code` / `day_index` **inchangés**. `contract_hours` reste `souhait`.

## Comportement

Uniquement les `message` du tableau freeze (`contract_hours`, `consecutive_rest_days`, `weekend_*`, `unavailability`, `max_daily_hours`, `max_coupure`, `weekly_rest_days`, `max_weekly_hours`, `assigned_on_closure`).  
Déjà FR : empty_post / max services / coupures / 11 h — **ne pas** retoucher. Cells recap **inchangées**.

## Tests

Un assert par code du tableau (sous-chaîne FR). Pytest domaine / engine / recap / board / hydrate verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core warn-fr pushed @ <sha>`
