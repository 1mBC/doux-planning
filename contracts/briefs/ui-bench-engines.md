# Brief — coller dans le chat **UI**

Le tech lead : Banc — **Compléter les trous** + loader **% / temps max** + **Exporter tout le banc**. File Infra close (`master has bench-engines landed` Infra). Relis **`contracts/domain/bench.md`** UI (Lancer + loader + export).

`git fetch origin` ; si `origin/bench-engines/infra` ≠ le SHA du signal Infra → **stop**.  
`git pull origin master` ; branche **`bench-engines/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-engines/ui` toi-même**. Message : `feat(web): bench gaps loader and bank export v0.39.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.39.0`**, note FR : banc, pack complet + trous + loader.

## Comportement

- Bouton **Compléter les trous** → `POST scope=gaps`. Pile unique, partir = OK.
- Loader si batch actif (`GET /v1/admin/bench/batches/active` au mount + après lot / gaps) : **%** + **temps max restant** (`eta_max_seconds`). Poll ~2 s, puis refresh versions.
- Les lancers lot (`all` / catégorie) utilisent aussi `batch_id` du 202.
- **Exporter tout le banc** → `scope=bank`, fichier `bench-bank.json`.
- Tableau / recap / lancer 2 lignes / v0.38 **inchangés** à part ça.

## Vérif

Build. `/admin/bench` : bouton trous ; overlay % + eta ; export bank download. Barre **v0.39.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-engines pushed @ <sha>, v0.39.0`
