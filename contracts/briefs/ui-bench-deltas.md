# Brief — coller dans le chat **UI**

Le tech lead : tableau Banc **inversé** + deltas colorés. **Attends le land Core** (`master has engine-seeds landed`) — le sous-titre montrera `core-3`. Relis **`contracts/domain/bench.md`** UI.

`git fetch origin` ; si `origin/engine-seeds/core` ≠ le SHA du signal Core → **stop**.  
`git pull origin master` ; branche **`engine-seeds/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync. **Pas d’Infra** (GET versions déjà là).

**Process** : tâches + `npm run build` vert → **commit + push `engine-seeds/ui` toi-même**. Message : `feat(web): bench deltas by model v0.37.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.37.0`**, note FR : banc, Manuel à gauche, deltas colorés par modèle.

## Comportement

```
Manuel | {engine_ref}                    | {engine_ref} | …
         Minimal | Optimisé | Maximal
```

- **Un** Manuel à gauche : note globale. Clic → compare `optimized` moteur courant.
- Cellule modèle × compute : **seulement** le delta vs Manuel. Tiret si pas de run. Clic → compare de **ce** `run_id`.
- Couleur : delta 0 = **vert** ; négatif = crescendo **rouge** (clamp −1) ; positif = crescendo **bleu** (clamp +1).
- Lancer / export / 50 lignes **inchangés**.

## Vérif

Build. `/admin/bench` : 1 colonne Manuel ; ensuite une famille par `engine_ref` (3 computes). Cellules = deltas colorés. Barre **v0.37.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-deltas pushed @ <sha>, v0.37.0`
