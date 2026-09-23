# Brief — coller dans le chat **Infra**

Le tech lead : exposer `score.resumes` sur chaque cycle (même objet que Core). **Attends le land Core** (`master has score-chrome landed`). Relis `contracts/domain/score.md` + `v1-generate.md`.

`git fetch origin` ; si `origin/score-chrome/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score-chrome/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync. Pas d’Alembic.

**Process** : tâches + pytest vert → **commit + push `score-chrome/infra` toi-même**. Message : `feat(api): emit score resumes on generate and cycles`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. Reste `api/` + TestClient.

## Comportement

- Chaque cycle non null (POST generate 200 / job done / GET cycles / hydrate) : `score` = forme `score.md` **avec** `resumes`.
- Vieux JSONB avec `score` sans `resumes` : GET hydrate via Core (comme recap), pas 500, pas d’objet partiel.
- Exemple public **92** : GET peut omettre `score` (hors rewrite snapshot).
- Keep-best / jobs / versions **inchangés**. Clé `contrat` inchangée.

## Tests

POST minimal → `score.resumes` a les 5 clés. GET cycles idem. Cycle stocké avec `score` sans `resumes` → GET hydrate les resumes. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra score-chrome pushed @ <sha>`
