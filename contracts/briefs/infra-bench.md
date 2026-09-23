# Brief — coller dans le chat **Infra**

Le tech lead : HTTP admin banc + persist **chaque** run + jobs Maximal/all. **Attends le land Core** (`master has bench landed`). Relis `contracts/domain/bench.md`.

`git fetch origin` ; si `origin/bench/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync. **Alembic** : `bench_jobs` + `bench_runs`.

**Process** : tâches + pytest vert → **commit + push `bench/infra` toi-même**. Message : `feat(api): admin bench runs and jobs`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**` (lecture), `saint-cloud.json`. Reste `api/` + TestClient.

## Comportement

- Routes `bench.md`. Admin only. `app_version` = trim `data/bench/VERSION`.
- Sync : `scope=dataset` + minimal|optimized → 200 + row `bench_runs`.
- 202 : `all` | `category` | `maximal` — un `bench_jobs` par jeu. Worker (même process, **autre** table) : `run_bench` → persist run. UI partie → quand même `done` + row.
- **Pas** de 409 avec `generate_jobs` resto. **Pas** d’écriture `published_cycles` / `generate_logs`.
- SPA : `/admin`, `/admin/bench`, `/admin/bench/{category}/{dataset_id}/{search_effort}`.
- Tests : **tick stub** pour Maximal ; pas d’attente 600 s. Un generate resto `minimal` inchangé.

## Tests

POST dataset minimal → 200 + GET runs. POST all maximal 202 + tick stub → 4 runs. GET compare. 403 non-admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench pushed @ <sha>`
