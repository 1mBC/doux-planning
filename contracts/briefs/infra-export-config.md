# Brief — coller dans le chat **Infra**

Le tech lead : **GET export + POST import** config resto (JSON `export_version: 1`). File polish close (`master has polish landed` @ `15869b5`, UI v0.18.0). Relis `contracts/domain/export-config.md` et `contracts/http/v1-context.md` (tu les suis, tu ne les modifies pas).

`git pull origin master` (plus récent que `15869b5`, doit contenir ce brief) ; branche **`export-config/infra` depuis `master`**. **Pas** de merge Core (pas de nouveau Python hors `api/`).

`/opsx-update` **`build-planning-api`**. Pas de `/opsx-update` seed / context / sandbox. Pas d’archive / sync. **Pas** d’Alembic. **Pas** de `generate_cycle`.

**Process** : tâches + pytest vert → **commit + push `export-config/infra` toi-même**. Message : `feat(api): context export and import config`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `context.py` Core, `saint-cloud.json`. Reste `api/` + TestClient. Reuse smash seed (published / linked / comptes salariés).

## Comportement

- `GET /v1/context/export` Bearer company → 200 `{ export_version: 1, name, services, ladders, employees sans token, types, typical_week }`. Jamais `company_code` / `invite_token`.
- `POST /v1/context/import` Bearer company, body = cette forme → smash comme seed + name du JSON + **nouveaux** tokens. 200 = Context GET. Version ≠ 1 → 400 `Champs invalides.` Clés interdites dans le body → **ignorer**.
- Employee 403, sans Bearer 401, sans DB 503. Exemple **92** inchangé.

## Tests

Scénarios du freeze (export strip, import smash + linked 401, version 2 → 400) + pytest api (auth / context / seed / exemple 92) verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra export-config pushed @ <sha>`
