# Brief — coller dans le chat **Infra**

Le tech lead : compare + **export pack** JSON banc. **Attends le land Core** (`master has bench-pack landed` — SHA du signal Core). Relis `contracts/domain/bench.md` (HTTP compare + export).

`git fetch origin` ; si `origin/bench-pack/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench-pack/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

Pas d’archive / sync. Pas d’Alembic (recompute recap).

**Process** : tâches + pytest vert → **commit + push `bench-pack/infra` toi-même**. Message : `feat(api): bench compare recap slices and export pack`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`. Reste `api/` + TestClient.

## Comportement

- GET compare : `{ employees, model: CycleSlice, manual: CycleSlice }` via `cycle_recap_from_draft` (assignments persistés + expected.json + contexte). **Plus** d’alias `facts` plats = warnings. Vieux rows OK (recompute).
- `GET /v1/admin/bench/export?scope=dataset&category=&dataset_id=` et `scope=below_manuel` — forme pack `bench.md`.
- `below_manuel` : jeux avec ≥1 effort `global modèle < global manuel` ; pack = **tous** les efforts run de ces jeux + manuel + context.
- 403 non-admin. Dataset sans run → 404. `below_manuel` vide → `datasets: []`.

## Tests

GET compare halles après un run minimal : `model.facts` et `manual.facts` ont des hits.  
GET export dataset + below_manuel 200. 403 sans admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-pack pushed @ <sha>`
