# Brief — coller dans le chat **Infra**

Le tech lead : exposer `score` sur chaque cycle (même objet que Core `cycle_recap`). **Attends le land Core** (`master has score landed`). Relis `contracts/domain/score.md` + `v1-generate.md`.

`git fetch origin` ; si `origin/score/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score/infra` depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py`.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync. Pas d’Alembic (JSONB / recap déjà calculé).

**Process** : tâches + pytest vert → **commit + push `score/infra` toi-même**. Message : `feat(api): emit cycle score on generate and cycles`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. Reste `api/` + TestClient.

## Comportement

- Chaque cycle non null (POST generate 200 / job done / GET cycles / hydrate recap manquant) : clé `score` = forme `score.md`.
- Vieux JSONB sans `score` : GET calcule via Core (comme recap), pas 500.
- Exemple public **92** : pas obligatoire d’écrire `score` dans le fichier ; GET exemple peut omettre `score` (hors rewrite snapshot).
- Keep-best / jobs / versions **inchangés**.

## Tests

POST minimal → slot a `score.notes` + `score.global` + `score.weights`. GET cycles idem. Cycle stocké sans `score` → GET hydrate. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra score pushed @ <sha>`
