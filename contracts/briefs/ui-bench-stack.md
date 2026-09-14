# Brief — coller dans le chat **UI**

Le tech lead : Banc — **computes empilés** dans chaque colonne modèle. File 45 close (`master @ 2299502`). Relis **`contracts/domain/bench.md`** UI (tableau).

`git pull origin master` ; branche **`bench-stack/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync. **Pas de Core / Infra.**

**Process** : tâches + `npm run build` vert → **commit + push `bench-stack/ui` toi-même**. Message : `feat(web): bench stack computes per model v0.41.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.41.0`**, note FR : banc, computes empilés par modèle.

## Comportement

- En-tête **une** ligne : une colonne par `engine_ref` (plus de `colSpan=3` / 2ᵉ rangée Mini|Opti|Max).
- Cellule modèle = **3 deltas verticaux** (Minimal, Optimisé, Maximal), petit libellé, même ordre que Lancer. Clic = compare de ce `run_id`.
- Colonne Lancer (par jeu) : `.bench-launch` en **colonne** (plus de wrap horizontal) + Exporter en dessous — pile = Minimal, Optimisé, Maximal, Exporter.
- Toolbar globale Lancer (Toutes les catégories / par compute) : **inchangée** (rangées horizontales).
- Manuel / recap / loader / gaps / export / `locked = busy \|\| exporting` **inchangés**.

## Vérif

Build. `/admin/bench` : 1 colonne `core-3` avec 3 lignes de delta alignées sur Lancer. Barre **v0.41.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-stack pushed @ <sha>, v0.41.0`
