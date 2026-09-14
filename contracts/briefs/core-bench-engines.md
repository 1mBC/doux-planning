# Brief — coller dans le chat **Core**

Le tech lead : **moteurs figés + `SearchTrace`**. File 43 close (`master` a ce brief + `contracts/domain/engines.md`). Relis **`engines.md`** (gagne) et `bench.md` Core.

`git pull origin master` ; branche **`bench-engines/core` depuis `master`**.

`/opsx-update bench-datasets` (run_bench / VERSION) — pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-engines/core` toi-même**. Message : `feat(core): vendor core-0..2 engines and search trace`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 bit-à-bit**. Keep-best / seeds / `SEARCH_*` / `VERSION` **`core-3` inchangés**.

## Comportement

- `engines/core_0.py` ← `engine.py` @ `dd23c4b81fc2d88769b36273e414281ff3d03aca`
- `engines/core_1.py` ← `420cd6b452dfd9123e99e0210f90270be194ebfc`
- `engines/core_2.py` ← `f34ff3b2d0e998c4fa568f4ca3d0d7161c3bab72`
- Live `engine.py` = `core-3`. `list_engine_refs()` / `generate_for` / `UnknownEngineRef`.
- `run_bench(..., engine_ref=)` omis = VERSION. `BenchOutcome.trace` **toujours**.
- Live `generate_cycle` : `trace` du keep-best (seeder gagnant, locks, calendriers par seeder, infeasibles, `attempt_key`).
- Figés : `seeder=empty`, `n_locks=0`.

## Tests

`list_engine_refs() == ("core-0","core-1","core-2","core-3")`.  
`run_bench(tight, halles, minimal)` × 4 refs : `trace` complète, `engine_ref` demandé.  
`core-2` sans seeders. Ref inconnue → `UnknownEngineRef`.  
`engine_ref() == "core-3"`. 50 listings.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-engines pushed @ <sha>`
