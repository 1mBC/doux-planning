# Brief — coller dans le chat **UI**

Le tech lead : banc **50 jeux** (30 + 20 oracles). File Infra close (`master has bench-oracles landed` Infra). Relis **`contracts/domain/bench.md`** UI (liste = API).

`git fetch origin` ; si `origin/bench-oracles/infra` ≠ le SHA du signal Infra → **stop**.  
`git pull origin master` ; branche **`bench-oracles/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-oracles/ui` toi-même**. Message : `feat(web): bench shows fifty datasets v0.36.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.36.0`**, note FR : banc 50 jeux, 20 oracles crafted.

## Comportement

- Tableau + lancer : **aucun** 30 / 7 / 6 en dur. Source GET datasets / versions (**50** lignes, dont **26** `crafted`, ordre API).
- Barre « Lancer » : une rangée par catégorie listée (inchangé).
- Compare / export / 3 computes × versions **inchangés**. Pas de chrome worker.

## Vérif

Build. `/admin/bench` : **50** lignes ; 26 `crafted` ; lancer `crafted` Maximal enqueue sans casser. Barre **v0.36.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-oracles pushed @ <sha>, v0.36.0`
