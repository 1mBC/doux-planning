# Brief — coller dans le chat **Core**

Le tech lead : **catalogue banc ~30 jeux** — types multiples, 3 services, échelles jusqu’à L6. File 39 close (`master @ f5db183` ou plus récent). Relis **`contracts/domain/bench.md`** (gagne — Catalogue + `typical_week`).

`git pull origin master` (doit contenir ce brief + freeze) ; branche **`bench-widen/core` depuis `master`**.

`/opsx-update bench-datasets`. Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-widen/core` toi-même**. Message : `feat(core): widen bench catalogue to thirty datasets`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. **Pas** d’`engine.py` (fill / SAT / keep-best / `SEARCH_*` **inchangés**). `VERSION` **reste `core-2`**. Les 7 jeux existants **bit-à-bit inchangés**.

## Comportement

- `BENCH_CATEGORY_ORDER` : + `hours`, `size`, `overqual`, `closed`, `shapes`.
- `load` : si `typical_week` dans le JSON → l’utiliser ; sinon dérivation actuelle (1 type par service).
- **23** nouveaux dossiers `data/bench/{category}/{id}/` (context + expected) selon le tableau `bench.md`.
- `hours.services` peut inclure `morning`. Plusieurs `types` le même `service_id` si `typical_week` les départage.
- Rôles `level` jusqu’à **6**. Salle only.

## Tests

`list_bench_datasets` = **30**. Chaque paire du freeze : load + `evaluate(expected)` → 0 interdit.  
6 `crafted` : `cycle_score` expected `global >= 9.5`.  
≥ 4 nouveaux avec `morning` ; ≥ 4 avec 2 types le même service ; ≥ 4 avec un rôle `level >= 6`.  
Les 7 anciens : même `id` / mêmes assignments expected.  
`engine_ref() == "core-2"`. `run_bench(tight, halles, minimal)` vert.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-widen pushed @ <sha>`
