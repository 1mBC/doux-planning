# Brief — coller dans le chat **Infra**

Le tech lead : exposer **`facts[]`** sur chaque cycle, plus `warnings[].message` / `score.resumes` / `cell.text`. **Attends le land Core** (`master has score-facts landed` — SHA du signal Core). Relis `contracts/domain/score-facts.md` + `http/v1-generate.md` + `admin.md` + `v1-sandbox-edit.md` + `v1-examples.md`.

`git fetch origin` ; si `origin/score-facts/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score-facts/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

Pas d’archive / sync. Pas d’Alembic obligatoire (JSONB). Dual-read `generate_logs.warnings` → `facts` à la lecture.

**Process** : tâches + pytest vert → **commit + push `score-facts/infra` toi-même**. Message : `feat(api): emit score facts on generate cycles and logs`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`. Snapshot fichier = Core. Reste `api/` + TestClient.

## Comportement

- POST generate 200 / job done / GET cycles / hydrate / live sandbox / publish : cycle = `facts` + `score` **sans** `resumes` + cells `kind`/`payload`. **Plus** de clé `warnings`.
- Vieux JSONB `warnings`+`message` / `score.resumes` / `cell.text` : GET hydrate via Core (`cycle_recap`), pas 500.
- `_warning_json` → `_fact_json` (`axis`, `kind`, `polarity`, `severity`, `employee_id`, `day_index`, `payload`).
- `generate_logs` : persister misses evaluate + `employee_name`. GET `{ facts }`. Vieux rows : `score-facts.md` Hydrate (`message` last-resort).
- `bench_runs` : facts misses, score sans resumes.
- Sandbox HTTP impact : facts, pas `message`.
- GET saint-cloud : dual-read fichier Core (92, 17 misses).
- Keep-best / jobs / versions **inchangés**.

## Tests

POST minimal → `facts` array, pas `warnings`, pas `score.resumes`. GET cycles idem.  
Cycle stocké ancien `warnings` → GET émet `facts` hydratés.  
Admin generates : `facts` + `employee_name`. Preview sandbox : impact sans `message`.  
Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra score-facts pushed @ <sha>`
