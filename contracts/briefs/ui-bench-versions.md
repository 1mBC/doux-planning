# Brief — coller dans le chat **UI**

Le tech lead : admin **Versions** — matrice Maximal par `engine_ref`. File Infra bench-versions close (`master has bench-versions landed` Infra @ `2b5a9c6`). Relis **`contracts/domain/bench.md`** UI.

`git fetch origin` ; si `origin/bench-versions/infra` ≠ `2b5a9c6b2fb1a3d9fbcb5bd9e29c3220ba3b49d7` → **stop**.  
`git pull origin master` ; branche **`bench-versions/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-versions/ui` toi-même**. Message : `feat(web): admin bench versions matrix v0.33.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.33.0`**, note FR : banc versions moteur, matrice Maximal par `engine_ref`.

## Comportement

- Menu admin **à plat** : **Historique des computes | Banc | Versions**. Courante marquée. Routes `/admin/bench/versions` et `/admin/bench/run/{run_id}`.
- **Banc** : tableau last-run **inchangé**. Sous-titre `moteur {engine_ref}` (parser `engine_ref` ou `app_version`, même string).
- **Versions** : GET `/v1/admin/bench/versions`. Lignes = jeux, colonnes = `engine_refs`. Cellule = **Maximal** : globale + delta vs Manuel (tiret si null). Clic → `/admin/bench/run/{run_id}`.
- Page run : **même écran compare** que aujourd’hui, chargé via `GET /v1/admin/bench/runs/{run_id}` (pas le compare-chemin). Compare `/admin/bench/{cat}/{id}/{effort}` = last-run **courant**, inchangé.
- Pas de bouton revert. Export banc inchangé.

## Vérif

Build. Menu 3 entrées. Banc : sous-titre `moteur core-0`. Versions : une colonne `core-0` après un Maximal ; clic ouvre le compare de ce run (Modèle / Manuel). Barre **v0.33.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-versions pushed @ <sha>, v0.33.0`
