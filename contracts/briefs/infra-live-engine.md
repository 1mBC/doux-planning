# Brief — coller dans le chat **Infra**

Le tech lead : **`live_engine_ref`** — le moteur du `POST /v1/generate` client. **Attends le land Core** (`master has core-5+6 landed`). Relis **`contracts/domain/admin.md`** (gagne) + `generate-versions.md` + `v1-generate.md` + `team-generate.md` + `generate-jobs.md`.

`git fetch origin` ; si `origin/<branche Core>` ≠ le SHA du signal Core → **stop**.  
`git pull origin master` ; branche **depuis `master`**. **Pas** de merge UI. **Ne pas** retoucher `engine.py` ni `data/bench/**`.

`/opsx-update build-planning-api`. Pas d’archive / sync. **Alembic oui** (`live_engine` + `generate_logs.engine_ref`). JSONB cycles : pas d’Alembic (`engine_ref` dans le slot).

**Process** : tâches + pytest vert → **commit + push toi-même**. Message : `feat(api): admin live engine_ref for customer generate`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `data/bench/**`. Reste `api/` + Alembic + TestClient.

## Comportement

- GET/PUT `/v1/admin/live-engine` : `{ engine_ref, engine_refs }`. PUT inconnu → 400 `Moteur inconnu.` Non-admin 403.
- Unset / ref hors registre → effective = `VERSION`. **Pas** 500 sur generate.
- `POST /v1/generate` (sync + worker) : `generate_team(..., engine_ref=effective)`. Body **sans** `engine_ref`.
- Slot cycle + log : `engine_ref` du run. Vieux slots / rows : clé absente / null.
- Banc **inchangé** (toujours `VERSION` / job.engine_ref). Exemple 92 inchangé.

## Tests

GET unset → `engine_ref` = `core-5` (VERSION) + liste 7 refs.  
PUT `core-6` → GET `core-6`. PUT `core-9` → 400. Employee / non-admin → 403.  
POST minimal après PUT `core-2` → slot + log `engine_ref: core-2`.  
Vieux log sans colonne → `engine_ref` null. GET cycles slot neuf a `engine_ref`. Pytest api verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra live-engine pushed @ <sha>`
