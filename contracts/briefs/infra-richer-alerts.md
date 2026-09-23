# Brief — coller dans le chat **Infra**

Le tech lead : **merge only**. Core a poussé **`origin/alerts/core` @ `31b6313`**. Les textes d’alerte / wish viennent de `evaluate` + `cycle_recap` — le wrap generate/cycles **existe déjà**. Relis `contracts/domain/cycle-recaps.md` (tu le suis, tu ne le modifies pas).

`git fetch origin` ; si `origin/alerts/core` ≠ `31b6313048a383bbf66ee82a6a84f06d0b6feb9c` → **stop**, remonte.  
`git pull origin master` (plus récent que `5b01ae7`, doit contenir ce brief) ; branche **`alerts/infra` depuis `master`** ; merge **`origin/alerts/core`** (Python hors `api/` — ne pas réécrire ce merge).

**Pas** de `/opsx-update` richer-alerts / cycle-recaps / weekend-rest / sandbox. Pas d’archive / sync. **Pas** de nouvelle route, **pas** d’Alembic.

**Process** : pytest vert → **commit + push `alerts/infra` toi-même**. Message : `feat(api): merge richer-alerts core`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `context.py` Core, `saint-cloud.json`. Si un test HTTP pin un ancien `empty_post` anglais : **aligne l’assert** sur le message FR, ne change pas le wrap.

## Comportement

Aucun wrap nouveau. POST `/v1/generate` + GET `/v1/cycles` renvoient déjà `warnings[].message` et `wish_rows[].cells.*.text` du Core mergé.

## Tests

Pytest api (generate / cycles / auth / exemple 92) verts. Cuisine `null` intacte.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra alerts pushed @ <sha>`
