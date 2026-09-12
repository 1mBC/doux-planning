# Brief — coller dans le chat **Infra**

Le tech lead : banc **30 jeux** — `POST all` / catégories nouvelles. **Attends le land Core** (`master has bench-widen landed` — SHA du signal Core `33e05da`). Relis **`contracts/domain/bench.md`** (catalogue + HTTP : un job par jeu **listé**).

`git fetch origin` ; si `origin/bench-widen/core` ≠ `33e05dabdd605236764aace60b83504595c03965` → **stop**.  
`git pull origin master` ; branche **`bench-widen/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

`/opsx-update build-planning-api`. Pas d’archive / sync. **Pas d’Alembic**.

**Process** : tâches + pytest vert → **commit + push `bench-widen/infra` toi-même**. Message : `feat(api): bench all queues thirty datasets`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**`. Reste `api/` + TestClient. Routes **inchangées** (toujours `list_bench_datasets`).

## Comportement

- `POST scope=all` : **30** jobs (un par jeu listé).
- `scope=category` `crafted` : **6** jobs. `hours` / `size` / `overqual` / `closed` / `shapes` : acceptés (dans `BENCH_CATEGORY_ORDER` Core).
- GET datasets : 30, `engine_ref == "core-2"`.
- Tick stub Maximal : **pas** 30 × 600 s. Generate resto `minimal` inchangé.

## Tests

POST all maximal + stubs → **30** `job_ids` / 30 runs.  
POST `category=crafted` maximal → **6** jobs.  
GET datasets = 30. 403 non-admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-widen pushed @ <sha>`
