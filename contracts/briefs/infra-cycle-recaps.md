# Brief — coller dans le chat **Infra**

Le tech lead : persist recap sur `/v1/generate` + `/v1/cycles`. Core a poussé **`origin/recaps/core` @ `8f78a8c`**. Relis `contracts/domain/cycle-recaps.md` et `contracts/http/v1-generate.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/recaps/core` ≠ `8f78a8c080559fc9c401886181eb10bc550e3502` → **stop**, remonte.  
`git pull origin master` (plus récent que `9cc755c`, doit contenir ce brief) ; branche **`recaps/infra` depuis `master`** ; merge **`origin/recaps/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`**. **Pas** de `/opsx-update` `cycle-recaps` / weekend-rest-day / wellbeing / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `recaps/infra` toi-même**. Message : `feat(api): persist cycle_recap on generate/cycles`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `context.py` Core, `data/examples/saint-cloud.json`. Reste `api/` + TestClient. **Pas** d’Alembic.

## Comportement

- Wrappe **`cycle_recap`**. Ne pas recalculer stats / cellules dans `api/`.
- Cycle non null : `assignments`, `warnings`, `stats`, `legal_cols`, `legal_rows`, `wish_cols`, `wish_rows`. `null` = pas de recap.
- POST generate → persist JSONB → GET identique. Restart process → mêmes clés.
- Cycle **déjà** persisté sans recap : GET hydrate + `cycle_recap` (pas 500).
- `POST /v1/live/sandbox/{team}/publish` : même `published` (recap inclus).
- Joujou `/v1/sandbox/*` + exemple public **92** inchangés. Warning `rest_between_days` = `message` Core (déjà dans le merge).

## Tests

Register + context ready + POST generate `minimal` → 200 a `stats.assignments` = `len(assignments)`, `legal_rows` / `wish_cols` présents, pas de `we1j`.  
GET `/v1/cycles` identique après « restart » (re-GET).  
Cuisine `null` intacte. 409 si pas ready. Exemple 92 + auth verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra recaps pushed @ <sha>`
