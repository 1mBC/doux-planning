# Brief — agent Infra neuf (cloud) · change **bench-import** (file 71)

Le tech lead : **POST import** resto → jeu banc en base + preview. Relis `contracts/domain/bench-import.md` Infra (**gagne**) + `bench.md` liste. Tu ne modifies pas `contracts/`.

**Attends Core** : `run_bench_on` + `bench_dataset_from_json` sur ta base (`cloud_base_branch` = branche Core). Si absent → **stop**, remonte.

Instance **neuve**. Branche **`cursor/bench-import-infra-2843`**. **Ne merge pas** `master`. **Ne pas** réécrire Core. File 72 (DELETE / tombstone / filtre UI) **hors scope**.

`/opsx-update` **`build-planning-api`**. Alembic : table `bench_imported_datasets`.

**Ne pas toucher** `web/`, `engine.py` formules, `contracts/`, fichiers `data/bench/`. Reste `api/` + worker load + Alembic.

**Process** : pytest vert → **commit + push**. Message : `feat(api): import restaurant as bench dataset`. Signal le SHA.

## Comportement

- GET `/v1/admin/restaurants/{id}/import-preview`.
- POST `/v1/admin/bench/import` (cases, note /10 optionnelle, commentaire).
- `/versions` : catalogue puis importés ; clés `origin`, `comment`.
- Worker : jeu pas sur disque → DB → `run_bench_on`. Override globale persistée. Cuisine-only → 400 `Ce jeu n’a pas de salle.`
- **Pas** de DELETE (file 72).

## Tests

`skipif` sans DB. Preview flags. Import + override → `manual.global`. `include_runs` → last-run sans POST run. Cuisine-only run 400. 403 / 404. Catalogue halles toujours load disque. Échecs préexistants non « corrigés ».

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-import pushed @ <sha>`
