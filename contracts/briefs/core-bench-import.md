# Brief — agent Core neuf (cloud) · change **bench-import** (file 71)

Le tech lead : extraire **`run_bench_on`** + **`bench_dataset_from_json`** pour que l’Infra charge un jeu **hors disque**. Relis `contracts/domain/bench-import.md` Core (**gagne**). Tu ne modifies pas `contracts/`.

**Attends** file 70 landé sur master. Instance **neuve**. Branche **`cursor/bench-import-core-2843`** depuis **master**. **Ne merge pas** `master`.

Nouveau change OpenSpec **`bench-import`**. Skills → propose puis `/opsx-apply`. Pas d’archive / sync.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `data/bench/` fichiers. Catalogue 50 **bit-à-bit**. `run_bench` disque **inchangé** pour l’appelant (délègue à `run_bench_on`).

**Process** : pytest vert → **commit + push**. Message : `feat(core): run_bench_on and bench_dataset_from_json`. Signal le SHA.

## Comportement

- `run_bench_on(dataset, effort, engine_ref=None)` = le corps actuel de `run_bench` (salle only, pas d’écriture `published_cycles`).
- `run_bench(...)` = load disque puis `run_bench_on`.
- `bench_dataset_from_json(...)` : `_load_context` + assignments (liste **vide** OK).

## Tests

`run_bench_on(load_bench_dataset("tight","halles"), minimal)` **égal** `run_bench(...)`. Empty expected ne lève pas. Catalogue 50 / `engine_ref` inchangés. **Interdit** de lire Postgres.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-import pushed @ <sha>`
