# Brief — coller dans le chat **Infra**

Le tech lead : jobs **`engine_ref`** + **`trace`** + **gaps** + **batch progress** + export **`bank`**. **Attends le land Core** (`master has bench-engines landed`). Relis **`contracts/domain/engines.md`**, **`bench.md` HTTP**, **`worker-queue.md`**.

`git fetch origin` ; si `origin/bench-engines/core` ≠ le SHA du signal Core → **stop**.  
`git pull origin master` ; branche **`bench-engines/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py` ni `data/bench/**`.

`/opsx-update build-planning-api`. Pas d’archive / sync. **Alembic oui** (`trace`, `engine_ref`, `batch_id`, `started_at`, unique partiel 4-clés).

**Process** : tâches + pytest vert → **commit + push `bench-engines/infra` toi-même**. Message : `feat(api): bench engine_ref jobs, gaps batch, bank export`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**`. Reste `api/` + Alembic + TestClient.

## Comportement

- Worker : `run_bench(..., engine_ref=job.engine_ref)` ; persist `trace`.
- POST `all` / `category` / dataset Maximal / **`scope=gaps`** : un `batch_id`, 202 `{ batch_id, job_ids, total, status }`. Gaps : 50 × 3 × 4 moins les last-run **avec** `trace` complète. 0 trou → 200 total 0.
- GET `/v1/admin/bench/batches/{id}` et `/batches/active` : `pct`, `eta_max_seconds` (formule freeze).
- GET export `scope=bank` : tous refs, `trace` incluse.
- GET versions : `engine_refs` = registre. GET run : `trace`.
- Dédup `(category, dataset_id, effort, engine_ref)`. `started_at` au claim.
- Tick stub : **pas** 600 × 600 s. Generate resto inchangé.

## Tests

POST gaps stub → `batch_id`, jobs = trous. 2× même clé → 1 job. 2 refs → 2 jobs.  
GET batch pct / eta. GET bank 200. GET versions 4 refs. 403 non-admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-engines pushed @ <sha>`
