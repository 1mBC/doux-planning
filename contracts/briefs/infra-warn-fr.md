# Brief — coller dans le chat **Infra**

Le tech lead : **merge only**. Core a poussé **`origin/warn-fr/core` @ `0b351c2`**. Landé sur master @ **`09855b0`** (`master has warn-fr landed`). Les `evaluate.message` FR passent déjà par generate/cycles. Relis `contracts/domain/cycle-recaps.md` section **Warnings restants FR** (tu le suis, tu ne le modifies pas).

`git fetch origin` ; si `origin/warn-fr/core` ≠ `0b351c23ada2517877f6cdc30bb68582696594d4` → **stop**, remonte.  
`git pull origin master` (plus récent que `09855b0`, doit contenir ce brief) ; branche **`warn-fr/infra` depuis `master`** ; merge **`origin/warn-fr/core`** (déjà dans master — ne pas réécrire ce merge).

**Pas** de `/opsx-update` warn-fr / richer-alerts / cycle-recaps / sandbox. Pas d’archive / sync. **Pas** de nouvelle route, **pas** d’Alembic.

**Process** : pytest vert → **commit + push `warn-fr/infra` toi-même**. Message : `feat(api): merge warn-fr core`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `context.py` Core, `saint-cloud.json` (snapshot **reste** EN). Si un test HTTP pin un ancien message anglais (`has … contract`, `missing two consecutive…`) : **aligne l’assert** sur le FR du freeze, ne change pas le wrap.

## Comportement

Aucun wrap nouveau. POST `/v1/generate` + GET `/v1/cycles` + live sandbox qui ré-évalue : `warnings[].message` = Core mergé. `/v1/examples/saint-cloud` inchangé.

## Tests

Pytest api (generate / cycles / live / auth / exemple 92) verts. Cuisine `null` intacte.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra warn-fr pushed @ <sha>`
