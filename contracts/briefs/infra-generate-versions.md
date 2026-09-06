# Brief — coller dans le chat **Infra**

Le tech lead : **3 slots** de cycle (minimal / optimized / maximal) + `generated_at` + **logs worker**. File polish close (`master has planning-polish landed` @ `71b6bfa`, UI v0.22.0). Relis `contracts/domain/generate-versions.md` + `v1-generate.md` (tu les suis, tu ne les modifies pas). `v1-me-planning.md` `latest` ; `v1-live-sandbox.md` enter `search_effort`.

`git pull origin master` (plus récent que `71b6bfa`, doit contenir ce brief) ; branche **`generate-versions/infra` depuis `master`**. **Pas** de merge Core. **Pas** de `engine.py` / `SEARCH_*`.

`/opsx-update` **`build-planning-api`**. Pas de `/opsx-update` generate-jobs / coerce. Pas d’archive / sync. **Pas** d’Alembic (JSONB). Logs worker = stdout.

**Process** : tâches + pytest vert → **commit + push `generate-versions/infra` toi-même**. Message : `feat(api): persist generate versions and worker logs`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. Reste `api/` + worker + TestClient.

## Comportement

- `published[team]` = `{ versions: { minimal, optimized, maximal }, latest }`. Chaque cycle : recap + `generated_at` + `search_effort`.
- POST / job done : écrit **ce** slot seulement, `generated_at` now, `latest` = plus récent.
- Coerce plat ancien → `versions.optimized`, `latest: optimized`.
- `GET /v1/me/planning` = `versions[latest]`.
- `enter` : `search_effort` (défaut latest). Publish : même slot, `generated_at` **inchangé**.
- Worker + uvicorn : logs ISO (start, job pris, generate start/end + durée, 202 / done / failed).
- Exemple **92**.

## Tests

Vieux JSONB plat → GET versions.optimized + latest optimized. POST minimal puis optimized → 2 slots, latest optimized, minimal intact. me/planning = latest. Enter sans effort = latest ; enter `minimal` ; publish minimal ne touche pas optimized. Worker tick : une ligne log start + done. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra generate-versions pushed @ <sha>`
