# Brief — coller dans le chat **Infra**

Le tech lead : **jobs Maximal** (hybride C). File nuit close (`master has coerce-railway landed` @ `e5b13a3`). Relis `contracts/domain/generate-jobs.md` + `contracts/http/v1-generate.md` (tu les suis, tu ne les modifies pas). `deploy/railway.md` worker.

`git pull origin master` (plus récent que `e5b13a3`, doit contenir ce brief) ; branche **`generate-jobs/infra` depuis `master`**. **Pas** de merge Core.

`/opsx-update` **`build-planning-api`**. Pas de `/opsx-update` coerce / admin / export. Pas d’archive / sync. **Alembic OK** (`generate_jobs`). Compose **`worker`**.

**Process** : tâches + pytest vert → **commit + push `generate-jobs/infra` toi-même**. Message : `feat(api): maximal generate job and worker`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. Reste `api/` + Alembic + Compose + Dockerfile commande worker + TestClient.

## Comportement

- `POST /v1/generate` `minimal` / `optimized` (omis = optimized) → **200** sync inchangé + log 200.
- `maximal` → **202** `{ job_id, team, search_effort, status: queued, estimated_seconds: 600 }`. **Pas** de solve dans uvicorn.
- `GET /v1/generate/jobs/{id}` Bearer company même resto → queued|running|done|failed. `published` seulement si `done`. 404 / 403 / 401 / 503 comme le freeze.
- Worker : SKIP LOCKED → `generate_team` maximal → persist cycles + **log** si succès. 409 ready → pas de job. 2ᵉ maximal même team queued/running → 409 `Un calcul maximal est déjà en cours.`
- Tests : tick worker **stub** (0 s). **Interdit** d’attendre 600 s.

## Tests

Salle ready : POST `minimal` 200 comme avant. POST `maximal` 202 + GET `queued` ; tick stub → `done` + `published.salle` + 1 log. 2ᵉ maximal pendant queued → 409. Cuisine pas ready → 409, 0 job. Employee GET/POST job 403. Autre company 404. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra generate-jobs pushed @ <sha>`
