# Brief — coller dans le chat **Infra**

Le tech lead : `POST all` compte **7** jeux. **Attends le land Core** (`master has bench-crafted landed`). Relis `contracts/domain/bench.md`.

`git fetch origin` ; si `origin/bench-crafted/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench-crafted/infra` depuis `master`**. **Pas** de merge UI.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync. **Pas** d’Alembic.

**Process** : tâches + pytest vert → **commit + push `bench-crafted/infra` toi-même**. Message : `test(api): bench all queues seven datasets`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**`. Routes **inchangées**.

## Comportement

- `POST /v1/admin/bench/run` `scope=all` : un job **par** jeu listé (7 aujourd’hui).
- `scope=category` `crafted` : 3 jobs.
- Reste identique (admin, persist, pas de published_cycles).

## Tests

POST all maximal + tick stub → **7** `job_ids` / **7** runs. POST category crafted minimal|… selon sync/202 du freeze. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-crafted pushed @ <sha>`
