# Brief — coller dans le chat **Core**

Le tech lead : **`core-3`** — seeds → SAT (locks) → fill, plus fill **anti-coupure**. File 41 close (`master` a ce brief + `contracts/domain/engine-seeds.md`). Relis **`engine-seeds.md`** (gagne).

`git pull origin master` ; branche **`engine-seeds/core` depuis `master`**.

`/opsx-update wellbeing-model` (generate_cycle / fill). `VERSION` + `engine_ref` : même change ou `bench-datasets` si tu y touches — **pas** de nouveau change OpenSpec. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `engine-seeds/core` toi-même**.  
**Le message de commit DOIT contenir la spec** (pipe, T=3, seeders, fill anti-coupure, compute). Titre : `feat(core): core-3 seeders then SAT then fill`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés**.

## Comportement

- `data/bench/VERSION` → **`core-3`**.
- Pipe `engine-seeds.md` : 5 seeders, locks, SAT contraint, fill trous, keep-best.
- `SEED_TIGHT_THRESHOLD = 3`.
- Fill : retirer `int(not started_day)` de `_soft_penalty` ; pénaliser la **création de coupure**. Fewest-first **reste**.
- Compute : minimal = empty + 16 calendriers ; opti = 10× seeders (empty ×1) + 320 round-robin / 30 s ; maximal = 50× + 10 min.

## Tests

`engine_ref() == "core-3"`.  
`minimal` : 0 lock, 16 max. Lock non déplacé par fill. Seed infeasible ignoré.  
`run_bench(tight, halles, minimal)` vert. 50 listings. Pytest moteur verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core engine-seeds pushed @ <sha>`
