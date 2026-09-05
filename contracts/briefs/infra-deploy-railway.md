# Brief — coller dans le chat **Infra**

Le tech lead : recette **Railway**, même origine. Relis `contracts/deploy/railway.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; branche **`deploy/infra` depuis `master`**.

Nouveau change OpenSpec **`deploy-railway`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox / generate / auth. Pas d’archive / sync. Pas de commit tant que le facteur ne le demande pas — **puis** commit + push `deploy/infra` (gate merge).

**Ne pas toucher** `web/src/` (sauf si le build Docker l’exige : alors **stop**, remonte). Pas de `contracts/`. Pas de formules moteur. Compose **local** inchangé (ports Bastien).

## Comportement

- Dockerfile **multi-stage** : build Vite `web/` → `dist` dans l’image API.
- FastAPI sert `dist` + fallback SPA (`/planning`, `/login`, `/register`, `/context`, `/exemple`) **sans** avaler `/v1`.
- uvicorn `0.0.0.0` + `$PORT` (défaut 8000). `alembic upgrade head` au boot si `DATABASE_URL`.
- Si Railway fournit `postgres://`, normaliser vers `postgresql+psycopg://` **dans `api/` seulement**.
- `railway.toml` (ou équivalent repo) : builder Dockerfile, rien d’autre inventé.
- Sans `dist` : TestClient `/v1` inchangé (exemple, auth skip, etc.).
- **Zéro** appel Railway dans les tests. Pas de GitHub Action.

## Tests

`npm`/image : `GET /v1/examples/saint-cloud` 92 après build image **ou** TestClient local sans dist toujours 200/92. Une requête SPA (`/planning`) sert `index.html` **si** `dist` est là (test optionnel skip si absent). Dual-read sans `DATABASE_URL` intact. Pytest existants verts.

Tâches cochées + pytest vert → commit + push `deploy/infra` → stop.
