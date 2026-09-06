# Brief — coller dans le chat **Infra**

Le tech lead : **admin** — promote `ADMIN_EMAIL` + log des generate **200**. File export-planning close (`master has export-planning landed` @ `a3af6be`, UI v0.20.0). Relis `contracts/domain/admin.md` (tu le suis, tu ne le modifies pas). `v1-auth.md` `me.admin` + `deploy/railway.md` env.

`git pull origin master` (plus récent que `a3af6be`, doit contenir ce brief) ; branche **`admin/infra` depuis `master`**. **Pas** de merge Core.

`/opsx-update` **`build-planning-api`**. Pas de `/opsx-update` generate / auth / export. Pas d’archive / sync. **Alembic OK** (`is_admin` + `generate_logs`). **Pas** de `kind: admin` au register. **Ne pas** créer de compte si l’email n’existe pas.

**Process** : tâches + pytest vert → **commit + push `admin/infra` toi-même**. Message : `feat(api): admin promote and generate logs`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. Reste `api/` + Alembic + TestClient.

## Comportement

- Boot : `ADMIN_EMAIL` → promote restaurateur existant (`is_admin`), idempotent.
- `me.admin` true/false. Register / login **inchangés** (`kind` company|employee).
- `POST /v1/generate` **200** seulement → une ligne log (email, nom resto, team, `warnings[]`).
- `GET /v1/admin/generates` Bearer admin → `{ entries }` newest-first. Non-admin → 403 `Action réservée à l’admin.`

## Tests

Promote 2× le même email → un seul compte, `admin: true`. Email inconnu → aucun insert. Generate 200 → +1 log ; 409 ready → pas de log. GET admin vide puis 2 generate → ordre newest-first. Company non admin / employee → 403. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra admin pushed @ <sha>`
