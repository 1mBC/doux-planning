# Brief — coller dans le chat **Infra**

Le tech lead : banc **`engine_ref`** — last-run par version, matrice, compare d’un run. **Attends le land Core** (`master has bench-versions landed` — SHA du signal Core `a496425`). Relis **`contracts/domain/bench.md`** (gagne — Identité + HTTP).

`git fetch origin` ; si `origin/bench-versions/core` ≠ `a496425` → **stop**.  
`git pull origin master` ; branche **`bench-versions/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

Pas d’archive / sync. **Pas d’Alembic** (colonne `bench_runs.app_version` = `engine_ref`).

**Process** : tâches + pytest vert → **commit + push `bench-versions/infra` toi-même**. Message : `feat(api): bench engine_ref versions and run compare`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**` (lecture). Reste `api/` + TestClient.

## Comportement

- Persist : `row.app_version = outcome.engine_ref` (plus relire VERSION à part).
- Summaries, GET datasets, GET runs : `engine_ref` **et** `app_version` = **le même string**. Vieux `"0.27.0"` **lu** comme `"core-0"`.
- **Last-run** = plus récent par `(category, dataset_id, search_effort, engine_ref)`. Un run `core-1` n’écrase pas `core-0`.
- Compare chemin existant = last-run du **`engine_ref` courant** (VERSION). Pas de run courant → 404.
- `GET /v1/admin/bench/runs/{run_id}` : **même 200 que compare** (`employees`, `model`, `manual`). Plus d’alias plats `assignments` / `facts`. 404 id inconnu.
- `GET /v1/admin/bench/versions` : forme `bench.md` (refs fusionnées, 3 efforts toujours présents, `null` si pas de run).
- Export dataset / `below_manuel` = last-run **courant** seulement. Pack + chaque effort : `engine_ref`, `run_id` ; racine `engine_ref` + `app_version` identiques.
- SPA : `/admin/bench/versions` + `/admin/bench/run/{run_id}` → `index.html` (en plus des paths déjà là).
- 403 non-admin. Keep-best / jobs / generate resto **inchangés**.

## Tests

Après un run halles minimal : summaries / datasets / export ont `engine_ref == app_version == "core-0"`.  
GET `/runs/{id}` = `model` + `manual` (hits).  
Insert d’un 2ᵉ row même jeu/effort `app_version="core-1"` : GET versions a **deux** refs ; compare chemin halles/minimal = le run **courant** (`core-0`).  
Row `0.27.0` lu comme `core-0`. 403 sans admin. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-versions pushed @ <sha>`
