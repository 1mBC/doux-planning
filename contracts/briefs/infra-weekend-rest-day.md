# Brief — coller dans le chat **Infra**

Le tech lead : persist / GET `weekend_rest_day`. Core a poussé **`origin/weekend-rest/core` @ `4f1a862`**. Relis `contracts/domain/wellbeing.md`, `contracts/http/v1-context.md`, `contracts/http/v1-me-planning.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/weekend-rest/core` ≠ `4f1a86284c979abd25802b5a27e4be6b00f113f1` → **stop**, remonte.  
`git pull origin master` (plus récent que `173aff3`, doit contenir `e1063d4` + ce brief) ; branche **`weekend-rest/infra` depuis `master`** ; merge **`origin/weekend-rest/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`**. **Pas** de `/opsx-update` `weekend-rest-day` / wellbeing-model / seed / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `weekend-rest/infra` toi-même**. Message : `feat(api): persist wellbeing.weekend_rest_day`. Pas de PR master. Signal le SHA. L’orchestrateur landera plus tard.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `staff.py`, `hydrate.py`, `data/examples/saint-cloud.json`. Reste `api/` + TestClient. **Pas** d’Alembic (JSONB objet déjà). Pas de coerce-on-read des vieux comptes Railway.

## Comportement

- Wrap JSONB : `Wellbeing.weekend_rest_day` aller-retour. PATCH `employees[].wellbeing.weekend_rest_day` → persist → GET identique.
- Clé absente → `false` (défaut Core). GET context expose toujours le bool.
- `at_least_one_weekend_rest_day` (et autres clés retirées) → 400 `Champs invalides.` Pas d’alias.
- `GET /v1/me/planning` : wish `{ kind: "weekend_rest_day", held }` si la case est posée (BoardWish Core). Ne pas filtrer le kind.
- Seed / exemple public : **92 / 17 / 10/12** inchangés.

## Tests

PATCH fiche `weekend_rest_day: true` → GET context `true` ; restart process → encore `true`.  
PATCH wellbeing sans la clé → GET `false`.  
PATCH ancienne clé liste → 400.  
Generate + publish + login salarié : GET `/v1/me/planning` a le wish `weekend_rest_day` si true.  
Auth / context / seed / exemple 92 verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra weekend-rest pushed @ <sha>`
