# Brief — coller dans le chat **Infra**

Le tech lead : **admin** enrichi (`search_effort`, `duration_seconds`, `employee_name` sur chaque warning) + `duration_seconds` sur les **slots** de cycle. File chrome close (`master has planning-chrome landed` @ `2ef7548`, UI v0.23.0). Relis `contracts/domain/admin.md` + `generate-versions.md` (tu les suis, tu ne les modifies pas).

`git pull origin master` (plus récent que `2ef7548`, doit contenir ce brief) ; branche **`admin-recap/infra` depuis `master`**. **Pas** de merge Core.

`/opsx-update` **`build-planning-api`**. Pas d’archive / sync. **Alembic OK** (`generate_logs.search_effort`, `generate_logs.duration_seconds`). JSONB cycles : pas d’Alembic.

**Process** : tâches + pytest vert → **commit + push `admin-recap/infra` toi-même**. Message : `feat(api): generate log effort duration and warning names`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json`. **Pas** de delete salarié / unlink. Reste `api/` + Alembic + TestClient.

## Comportement

- Mesurer le wall-clock du `generate_team` (sync **et** worker).
- Log 200 / job done : `search_effort`, `duration_seconds`, chaque warning + `employee_name` (fiche à cet instant, sinon null).
- GET `/v1/admin/generates` expose ces clés. Vieux rows : effort / durée **null**.
- Slot cycle : `duration_seconds` à côté de `generated_at`. GET cycles / POST / job done. Vieux slots : clé absente.
- Exemple **92**.

## Tests

POST minimal → log a `search_effort: minimal`, `duration_seconds` ≥ 0, warning avec `employee_name` si id. GET admin : mêmes clés ; row ancienne sans colonnes → null. GET cycles slot tout neuf a `duration_seconds`. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra admin-recap pushed @ <sha>`
