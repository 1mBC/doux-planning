# Brief — coller dans le chat **Infra**

Le tech lead : **pile workers N replicas** + `POST all` = 50. **Attends le land Core** (`master has bench-oracles landed` — SHA du signal Core). Relis **`contracts/domain/worker-queue.md`** (gagne) et `bench.md` HTTP (50 / 26).

`git fetch origin` ; si `origin/bench-oracles/core` ≠ le SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench-oracles/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py` ni `data/bench/**`.

`/opsx-update build-planning-api`. Pas d’archive / sync. **Alembic oui** (`heartbeat_at` + unique partiel).

**Process** : tâches + pytest vert → **commit + push `bench-oracles/infra` toi-même**. Message : `feat(api): safe parallel workers and fifty bench jobs`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**`. Reste `api/` + Alembic + TestClient.

## Comportement

- `heartbeat_at` sur `generate_jobs` et `bench_jobs`. Beat **10 s** pendant generate **et** banc.
- Reclaim : **seulement** `running` dont le heartbeat a plus de **180 s** (ou `NULL`). **Interdit** de requeue tous les `running` au start (le bug actuel).
- Reclaim au start **et** chaque tour de boucle.
- Unique partiel banc `(category, dataset_id, search_effort)` sur `queued`/`running`. Enqueue idempotent (même `job_id`).
- `POST scope=all` : **50** jobs (un par jeu listé). `scope=category` `crafted` : **26**.
- Compose / Railway : doc replicas déjà dans le freeze ; `docker compose --scale worker=N` doit marcher sans autre change (1 job / process).
- Tick stub Maximal : **pas** 50 × 600 s. Generate resto `minimal` / 409 maximal **inchangés**.

## Tests

Deux ticks concurrents → 2 jobs distincts.  
Reclaim 0 si heartbeat frais ; reclaim 1 si heartbeat vieux.  
Start + `running` frais → pas de steal.  
2× POST même jeu Maximal → 1 job.  
POST all maximal + stubs → **50** `job_ids`. POST `crafted` → **26**.  
GET datasets = 50, `engine_ref == "core-2"`. 403 non-admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra worker-queue pushed @ <sha>`
