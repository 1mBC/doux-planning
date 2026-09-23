# Brief — coller dans le chat **Infra**

Le tech lead : HTTP seed exemple. Core a poussé **`origin/seed/core` @ `bb9ac1d`**. Relis `contracts/domain/example-seed.md` et `contracts/http/v1-context.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/seed/core` ≠ `bb9ac1df921f4da72affad91fb797f99ff559508` → **stop**, remonte.  
`git pull origin master` (@ `95ac3a1` ou plus récent) ; branche **`seed/infra` depuis `master`** ; merge **`origin/seed/core`** (Python hors `api/` — ne pas réécrire ce merge).

`/opsx-update` **`build-planning-api`**. **Pas** de `/opsx-update` `example-seed` / wellbeing / sandbox. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `context.py` Core, `data/examples/saint-cloud.json`. Reste `api/` + TestClient. Pas de `hydrate_delivered_cycle`.

## Comportement

- `POST /v1/context/seed-example` Bearer **company**, **pas de body** → 200 **même** `Context` que GET (après smash).
- Wrappe `seed_example_context` Core. Persist : services, hours, ladders, types, typical_week, fiches (tokens Core), `week_labels` dérivé.
- **Écrase** tout le contexte y compris fiches **déjà liées**. **Pas** de 409 `Cette fiche a déjà un compte.` Vide `published_cycles`, `live_sandboxes`, `linked_employee_ids`. Supprime les comptes salariés / sessions de **cette** company (sinon login orphelin).
- Garde `companies.id`, `name`, `invite_code`, `legal_context_id`.
- Employee Bearer → 403 `Action réservée au restaurateur.` Sans DB → 503. Exemple public **92** inchangé.

Hors tranche : bouton UI, generate.

## Tests

Register company (nom `""` ou PATCH name) → POST seed → GET : `ready.salle` true, `ready.cuisine` false, services midday+evening, fiches exemple, `week_labels` `"ab"`, `published` vide (`GET /v1/cycles`).  
2ᵉ POST seed → encore published vide, nouveaux tokens.  
Company avec fiche liée + cycle publié → seed 200, linked vide, cycles nuls, salarié ancien token → 401.  
Employee / sans Bearer / sans DB : 403 / 401 / 503. Auth + exemple 92 verts.

Tâches cochées + pytest vert → stop.  
Signal : `Infra seed done, pytest <n> passed, no commit.`
