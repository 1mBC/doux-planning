# Brief — coller dans le chat **Infra**

Le tech lead : HTTP wellbeing. Core a poussé **`origin/wellbeing/core` @ `4005994`**. Relis `contracts/domain/wellbeing.md`, `contracts/http/v1-context.md`, `contracts/http/v1-me-planning.md`, `contracts/http/v1-examples.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/wellbeing/core` ≠ `400599478fd5d0686c16cf0e1200d05c63438789` → **stop**, remonte.  
`git pull origin master` (@ `2864425` ou plus récent) ; branche **`wellbeing/infra` depuis `master`** ; merge **`origin/wellbeing/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`** : wrap HTTP nouvelle forme. **Pas** de `/opsx-update` `wellbeing-model` / sandbox / generate / auth. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `staff.py`, `hydrate.py`, `data/examples/saint-cloud.json`. Reste `api/` + Alembic si besoin + TestClient.

## Comportement

- Construire `Wellbeing` / `Unavailability(weekday, service_id)` Core. `week_label_scheme(state)` → `week_labels` (`"ab"` | `"parity"`) sur **GET `/v1/context`** et **GET `/v1/me/planning`**. Ignoré en PATCH.
- PATCH/GET `employees[]` : `wellbeing` **objet** + `unavailabilities: [{ weekday, service_id }]`. Plus de liste de clés, plus de `every_morning` / `every_evening`.
- `GET /v1/me/planning` : `wishes` = `{ kind, held, value?, service_id?, limit? }` (BoardWish Core). Plus de `{ key }`.
- Persist JSONB `staff_fiches.wellbeing` = **objet**. Lecture : objet → parse ; `[]` / absent → `Wellbeing()` ; anciennes clés / `every_*` → 400 `Champs invalides.` Pas d’alias.
- `auth.py` / `_state_from_rows` : plus de `WellbeingPreference`. Les 4 ImportError doivent disparaître.
- Exemple public : le JSON Core (déjà dans le merge) → 200 **92 / 17 / 10/12 / 47**. Ne pas régénérer le fichier.

Hors tranche : bouton seed, onglets UI, formules moteur.

## Tests

PATCH fiche `wellbeing.weekend: "even"` → GET `week_labels: "parity"` ; `every_two` seul → `"ab"`. Indispo sans `service_id` → 400.  
`GET /v1/me/planning` : wishes `kind`, pas `key`.  
Exemple 92 + stats contrat. Auth / context / cycles / me/planning verts. Dual-read sans DB intact.

Tâches cochées + pytest vert → stop.  
Signal : `Infra wellbeing done, pytest <n> passed, no commit.`
