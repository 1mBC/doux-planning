# Brief — coller dans le chat **UI**

Le tech lead : Banc — **recap vs modèle précédent** + **lancer 2 lignes**. File 42 close (`master` a ce brief + `bench.md` UI). Relis **`contracts/domain/bench.md`** (Recap + Lancer).

`git pull origin master` ; branche **`bench-recap/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync. **Pas de Core / Infra.**

**Process** : tâches + `npm run build` vert → **commit + push `bench-recap/ui` toi-même**. Message : `feat(web): bench recap vs previous model v0.38.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.38.0`**, note FR : banc, recap vs modèle précédent + lancer 2 lignes.

## Comportement

- Au-dessus du tableau : un bloc par `engine_ref` **sauf le premier**. Pour chaque effort : **%** `100 × mean(global − prev.global) / 10`, **max**, **min** (intersection des jeux qui ont les deux runs). Couleurs = mêmes deltas. Vide → tiret.
- Lancer : **2 lignes** seulement. (1) Toutes les catégories + 3 efforts. (2) 3 dropdowns d’effort → catégories, clic = `scope=category`. Plus de rangée par catégorie.
- Tableau scores / export / 50 lignes **inchangés**.

## Vérif

Build. `/admin/bench` : recap `core-3 vs core-2` (si les deux ont des runs) ; lancer = 2 lignes ; dropdown Maximal → `crafted` enqueue. Barre **v0.38.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-recap pushed @ <sha>, v0.38.0`
