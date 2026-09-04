# Brief — coller dans le chat **Infra**

Le tech lead : HTTP generate + persist cycles. Core a fini `generate_team` (`generate/core`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/domain/team-generate.md` et `contracts/http/v1-generate.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/generate/core` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`generate/infra` depuis `master`** ; merge **`origin/generate/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`** section **4** : `POST /v1/generate` + `GET /v1/cycles` **sync**, wrappe `generate_team`. **Pas** de table `jobs`, **pas** de worker Compose, **pas** de `SKIP LOCKED`. Le vieux design jobs est **hors slice**. Pas de `/opsx-update` sandbox / context. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `planning.py` hors ce que Core a déjà livré, preview/fill. Reste `api/` + Alembic + TestClient.

## Comportement

- Bearer company. Employé 403. Dual-read : sans DB → 503 ; exemple 92 + sandbox public inchangés.
- `POST { team, search_effort? }` → `generate_team` → persist `published_cycles` → 200 `published` salle+cuisine. `TeamNotReady` → 409 français, zéro solve.
- `GET /v1/cycles` = persisté. Restart / `reset_engine` identique.
- Tests **minimal** seulement.

## Tests

Register + PATCH contexte salle ready (comme test context) → POST generate `minimal` : `published.salle.assignments` non vide, tous `team: salle`, cuisine `null`. POST cuisine → 409. Second POST salle remplace salle. `reset_engine` → même GET cycles. Employee 403. Exemple 92. Context GET / auth toujours verts.

Tâches section 4 (sync) cochées + pytest vert → stop.
