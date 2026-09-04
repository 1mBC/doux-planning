# Brief — coller dans le chat **Infra**

Le tech lead : HTTP grille employé. Core a fini `employee_board` (`employee/core`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/domain/employee-board.md` et `contracts/http/v1-me-planning.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/employee/core` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`employee/infra` depuis `master`** ; merge **`origin/employee/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`** tâche **5.3** : `GET /v1/me/planning` (pas `/me/shifts`). **Pas** evaluate/swap/rank. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `employee_board` Core, `/v1/sandbox/*`. Reste `api/` + TestClient.

## Comportement

- Bearer employee, `employee_id` session → `employee_board`. Company 403 FR salarié. Dual-read : sans DB → 503 ; exemple 92 inchangé.
- Body = freeze. Pas de token, pas de live sandbox.

## Tests

Register company + PATCH salle ready + generate `minimal` + register employee sur fiche A → GET planning : assignments salle **tous**, `employee_id` A, `contract` / `wishes` présents. Cran live non publié invisible. Company Bearer → 403. Pas de cycle cuisine / autre équipe vide OK. Exemple 92. Auth / cycles verts.

Tâches 5.3 cochées + pytest vert → stop.
