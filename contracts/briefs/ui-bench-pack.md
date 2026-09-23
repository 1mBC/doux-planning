# Brief — coller dans le chat **UI**

Le tech lead : **même pastilles** banc/live + layout titre / note+jauge / totaux + **export pack**. File Infra bench-pack close. Relis `contracts/domain/bench.md` UI + `score.md` UI.

`git fetch origin` ; si `origin/bench-pack/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench-pack/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-pack/ui` toi-même**. Message : `feat(web): bench same score notes and export pack v0.31.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.31.0`**, note FR : banc même notes, export pack, pastille titre puis note+jauge.

## Comportement

- `CycleScoreNotes` : (1) titre (2) note + jauge **même ligne** (3) totaux (4) clic miss puis hit. Partout.
- Compare : parser `model` / `manual` / `employees`. Les deux blocs = même composant avec facts complets (plus l’id à la place du nom).
- **Exporter ce jeu** (compare + ligne tableau) → GET `scope=dataset`. **Exporter sous le Manuel** (tableau) → GET `scope=below_manuel`. Download JSON, filenames `bench.md`.

## Vérif

Build. Compare : clic Occupation des deux côtés liste miss **et** hit. Pastille = titre au-dessus, note+jauge alignés. Export dataset télécharge un JSON `kind: bench-pack`. Barre **v0.31.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-pack pushed @ <sha>, v0.31.0`
