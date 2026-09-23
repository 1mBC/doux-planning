# Brief — coller dans le chat **UI**

Le tech lead : afficher les notes /10 + globale sur le planning company. **Attends le land Infra** (`master has score landed` Infra). Relis `contracts/domain/score.md`.

`git fetch origin` ; si `origin/score/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `score/ui` toi-même**. Message : `feat(web): cycle score notes v0.25.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.25.0`**, note FR : notes /10 sur le planning.

## Comportement

- `/planning` company (pas salarié, pas `/exemple` sauf si le payload a `score`) : les 5 notes + globale du **cycle affiché** (effort courant).
- `null` → tiret. Une décimale FR (`8,4`).
- Pas d’édition des poids. Pas de bench admin.

## Vérif

Build. Planning : notes visibles, cohérentes après (Re)Calculer. Switch d’effort = notes de **ce** slot. Barre **v0.25.0**. Exemple 92.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI score pushed @ <sha>, v0.25.0`
