# Brief — coller dans le chat **UI**

Le tech lead : panneau `/admin/bench` + page compare. **Attends le land Infra** (`master has bench landed` Infra). Relis `contracts/domain/bench.md` (section UI).

`git fetch origin` ; si `origin/bench/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master` + worker.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench/ui` toi-même**. Message : `feat(web): admin bench table and compare v0.28.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, `data/bench/`. Reste `web/`. **`0.28.0`**, note FR : banc admin 4 jeux.

## Comportement

- `/admin` : lien **Banc** (log generate **reste**). `me.admin` only.
- `/admin/bench` : lancer all | catégorie | jeu × 3 efforts. Tableau 4 lignes × 3 efforts = **dernier** run (globale · oracle · Δ). Clic → compare.
- Maximal / all / category : poll job ou GET runs ; quitter la page OK.
- `/admin/bench/{category}/{id}/{effort}` : généré puis oracle, notes, grilles lecture. Pas d’édition.
- Parser `score` / `resumes` déjà là. SPA déjà prévue Infra.

## Vérif

Build. Admin → Banc → lancer 1 jeu minimal → ligne table → clic compare (2 grilles). Barre **v0.28.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench pushed @ <sha>, v0.28.0`
