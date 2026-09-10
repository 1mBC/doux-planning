# Brief — coller dans le chat **Core**

Le tech lead : **identité moteur `core-0`**. File score-tables close (`master has score-tables landed` @ `1fa8d25` ou plus récent). Relis **`contracts/domain/bench.md`** (gagne — section Identité + Core).

`git pull origin master` (doit contenir ce brief + freeze `bench.md`) ; branche **`bench-versions/core` depuis `master`**.

Pas de nouveau change OpenSpec. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-versions/core` toi-même**. Message : `feat(core): bench engine_ref core-0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. **Pas** d’`engine.py` (fill / SAT / keep-best / `SEARCH_*` / `_attempt_key` **inchangés**).

## Comportement

- `data/bench/VERSION` = une ligne `core-0` (plus `0.27.0`).
- `engine_ref() -> str` = trim de ce fichier.
- `BenchOutcome.engine_ref` : `run_bench` le remplit avec `engine_ref()`.
- `list` / `load` / recap / deltas **inchangés**.

## Tests

`engine_ref() == "core-0"`.  
`run_bench(tight, halles, minimal).engine_ref == "core-0"` ; `facts` / `expected_facts` non vides comme aujourd’hui ; 0 interdit sur expected ; `published_cycles` intact.  
`generate_cycle` déterministe inchangé. Pytest engine / recap / bench verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-versions pushed @ <sha>`
