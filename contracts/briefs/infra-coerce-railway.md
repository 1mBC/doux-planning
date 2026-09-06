# Brief — coller dans le chat **Infra**

Le tech lead : **coerce-on-read** du vieux JSON wellbeing Railway. File admin close (`master has admin landed` @ `db8d9e1`, UI **v0.21.0**). Relis `contracts/domain/coerce-railway.md` (tu le suis, tu ne le modifies pas). `v1-context.md` persist + `wellbeing.md` mapping (lecture seulement).

`git pull origin master` (plus récent que `db8d9e1`, doit contenir ce brief) ; branche **`coerce-railway/infra` depuis `master`**. **Pas** de merge Core.

`/opsx-update` **`build-planning-api`**. Pas de `/opsx-update` admin / export / weekend-rest. Pas d’archive / sync. **Pas** d’Alembic.

**Process** : tâches + pytest vert → **commit + push `coerce-railway/infra` toi-même**. Message : `feat(api): coerce legacy wellbeing json on read`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `staff.py`, `hydrate.py`, `saint-cloud.json`. Reste `api/` + TestClient (surtout `wellbeing_codec.py` + load fiche).

## Comportement

- **Lecture** (GET context / export / generate / me/planning) : liste de clés, clés retirées, `every_*`, `service_id` null, `max_*_per_week` fiche → objet Core (table du freeze). GET **n’émet plus** l’ancien JSON.
- **Heal** : si JSONB ≠ objet neuf → `UPDATE` la fiche. 2ᵉ GET identique, plus de liste en base. Idempotent.
- **PATCH / import** : legacy → **400** `Champs invalides.` (pas de coerce à l’écriture).
- `[]` / absent → `Wellbeing()`. Objet déjà Core inchangé. Exemple **92**.

## Tests

Insert JSONB `["two_consecutive_rest_days","weekend_off_every_two_weeks","at_least_one_weekend_rest_day","max_two_coupures_per_week"]` → GET objet (`consecutive_rest`, `weekend: every_two`, `weekend_rest_day: true`, coupures 2) ; 2ᵉ GET identique ; row soignée.  
`no_evening_service` → `max_services.evening: 0`.  
Indispo `every_morning` + journée `service_id: null` (resto midi+soir) → lignes `morning` / `midday`+`evening`.  
PATCH liste / clé retirée / `every_*` → 400. Objet neuf PATCH/GET inchangé. Exemple 92. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra coerce-railway pushed @ <sha>`
