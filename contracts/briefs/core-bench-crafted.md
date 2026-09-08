# Brief — coller dans le chat **Core**

Le tech lead : catalogue **`crafted`** (3 témoins ≥ 9,5). File banc close (`master has bench landed` @ `1d21d47` ou plus récent). Relis `contracts/domain/bench.md` — tu le suis, tu ne le modifies pas.

`git pull origin master` (doit contenir ce brief + `data/bench/crafted/`) ; branche **`bench-crafted/core` depuis `master`**.

`/opsx-update` **`bench-datasets`**. Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-crafted/core` toi-même**. Message : `feat(core): list crafted bench datasets`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `data/bench/**` (lecture). **Pas** de HTTP. Keep-best inchangé.

## Comportement

- `BENCH_CATEGORY_ORDER` : `tight`, `clock`, `wishes`, `ladder`, **`crafted`**.
- `list_bench_datasets` : 7 jeux. Load / `run_bench` inchangés.

## Tests

Les 7 paires `(category, id)` du freeze. Expected 0 interdit.  
`load_bench_dataset("crafted", "atelier"|"rivoli"|"marais")` : `cycle_score` sur expected → `global >= 9.5`.  
`run_bench(tight, halles, minimal)` toujours vert.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-crafted pushed @ <sha>`
