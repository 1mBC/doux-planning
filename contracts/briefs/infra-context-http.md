# Brief — coller dans le chat **Infra**

Le tech lead : persist + HTTP contexte. Core a fini `onboarding-context` (`context/core`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/domain/restaurant-context.md` et `contracts/http/v1-context.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/context/core` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`context/infra` depuis `master`** ; merge **`origin/context/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`** : section **3 seulement** (persist contexte live). **Pas** section 4 jobs / generate, **pas** publish, **pas** `/me/shifts`. Pas de nouveau mega-change. Pas de `/opsx-update` sandbox / auth. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `planning.py`, `engine.py`, modules Core onboarding, preview/fill, hydrate Saint-Cloud. Reste `src/doux_planning/api/` + Alembic + tests TestClient.

## Comportement

- `GET` / `PATCH /v1/context` Bearer **company**. Session → resto. Employé 403. Dual-read : sans `DATABASE_URL` → 503 ; exemple public + sandbox inchangés.
- Register company déjà vide : GET = name `""`, services `[]`, ladders/types/week vides, `ready` faux, `legal_context_id` `"france"`, `company_code` = invite. Wrappe `empty_restaurant` / `team_ready`. **Zéro** `generate_cycle`.
- PATCH sections optionnelles, remplacement par clé. `ready` recalculé Core. Fiches : token Core à la création ; rotate toujours `POST /v1/staff/{id}/invite-token`. Invites public voit les fiches non liées.
- Persist restart-safe. Pas d’écriture snapshot exemple.

## Tests

Register company → GET vide + ready faux. PATCH name + échelles salle + 1 fiche + services + type + semaine ouverte → `ready.salle` true, `ready.cuisine` false ; reset_engine → même GET. Case ouverte sans type → salle faux. Employee Bearer → 403. `GET /v1/examples/saint-cloud` 92. Invites voit la fiche. Auth login/logout toujours verts.

Tâches section 3 (contexte) cochées + pytest vert → stop.
