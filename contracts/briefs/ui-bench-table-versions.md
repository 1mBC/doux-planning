# Brief — coller dans le chat **UI**

Le tech lead : **un seul tableau Banc** — les **trois** computes, une colonne par version moteur. Plus de page Versions. File banc versions close (`master has bench-versions landed` @ `6a813c4` ou plus récent). Relis **`contracts/domain/bench.md`** UI.

`git pull origin master` (doit contenir ce brief + freeze `bench.md`) ; branche **`bench-table-versions/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas de brief Core / Infra : `GET /v1/admin/bench/versions` a déjà les 3 efforts. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-table-versions/ui` toi-même**. Message : `feat(web): bench table all efforts per engine_ref v0.34.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.34.0`**, note FR : banc, tous les computes, une colonne par version moteur.

## Comportement

- Menu : **Historique des computes | Banc**. **Supprimer** Versions.
- `/admin/bench/versions` → `go("/admin/bench")`.
- Tableau Banc : source **`GET /versions`** (plus last-run du moteur courant seul).
- Pour **Minimal, Optimisé, Maximal** : sous-colonnes `Manuel | {engine_refs…}`. Manuel = `dataset.manual.global`. Cellule moteur = globale + delta ; tiret si null. Clic moteur → `/admin/bench/run/{run_id}`. Clic Manuel → compare-chemin de cet effort.
- Lancer / export / page run / compare-chemin **inchangés**. Pas de bouton revert.
- Après un launch, **recharger** `/versions` (le tableau doit montrer le nouveau run).

## Vérif

Build. Menu 2 entrées. Banc : 3 computes, sous chacun Manuel + `core-0` (et `core-1` si l’API en envoie deux). Clic `core-0` Maximal = compare de ce run. `/admin/bench/versions` ramène au Banc. Barre **v0.34.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-table-versions pushed @ <sha>, v0.34.0`
