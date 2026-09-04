# Brief — coller dans le chat **Infra**

Le tech lead : HTTP sandbox **live**. Core a fini enter/discard/publish + preview routés (`live/core`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/domain/live-sandbox.md` et `contracts/http/v1-live-sandbox.md` (tu les suis, tu ne les modifies pas). Shapes preview = `contracts/http/v1-sandbox-edit.md`.

`git fetch origin` ; si `origin/live/core` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`live/infra` depuis `master`** ; merge **`origin/live/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`** section **5.2** seulement : routes `/v1/live/sandbox/{team}/…`. **Pas** evaluate/swap/rank, **pas** `/me/shifts`, **pas** de worker. **Ne pas** modifier `/v1/sandbox/*`. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, preview_* Core, hydrate Saint-Cloud. Reste `api/` + Alembic + TestClient.

## Comportement

- Bearer company. Wrappe `enter_live_sandbox` / preview-apply-undo / `discard_live_sandbox` / `publish_live_sandbox`.
- `NoPublishedCycle` → 409 FR. Persist brouillons live, pas la table joujou.
- `/v1/sandbox/*` + exemple 92 inchangés (toujours sans auth).

## Tests

Register + PATCH salle ready + POST generate `minimal` → enter salle 200 ; enter cuisine 409. Preview retune + commit + undo + discard restaure le publié. Publish → `GET /v1/cycles` salle changée, cuisine null ; GET live 404. `reset_engine` restaure un brouillon encore ouvert. Employee 403. `POST /v1/sandbox/enter` sans Bearer 200. Exemple 92.

Tâches 5.2 live cochées + pytest vert → stop.
