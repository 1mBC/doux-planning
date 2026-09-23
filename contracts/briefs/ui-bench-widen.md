# Brief — coller dans le chat **UI**

Le tech lead : banc **30 jeux** — catégories nouvelles dans le tableau. File Infra bench-widen close (`master has bench-widen landed` Infra @ `dbb53f5`). Relis **`contracts/domain/bench.md`** UI (liste = API).

`git fetch origin` ; si `origin/bench-widen/infra` ≠ `dbb53f5204a8e8f340016a26b7afde8a120c5c2c` → **stop**.  
`git pull origin master` ; branche **`bench-widen/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-widen/ui` toi-même**. Message : `feat(web): bench shows thirty datasets v0.35.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.35.0`**, note FR : banc 30 jeux, nouvelles catégories.

## Comportement

- Tableau + lancer : **aucun** 7 / 4 catégories en dur. Source GET datasets / versions (30 lignes, ordre API).
- Barre « Lancer » : une rangée par catégorie listée (`hours`, `shapes`, …).
- Compare / export / 3 computes × versions **inchangés**.

## Vérif

Build. `/admin/bench` : **30** lignes ; catégories `hours` `size` `overqual` `closed` `shapes` visibles ; lancer une catégorie `shapes` ne casse pas. Barre **v0.35.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-widen pushed @ <sha>, v0.35.0`
