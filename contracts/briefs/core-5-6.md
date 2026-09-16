# Brief — coller dans le chat **Core Engine**

Le tech lead : **`core-5` + `core-6`**. Relis **`contracts/domain/engine-core-5.md`** (live, gagne) + **`engine-core-6.md`** + **`engines.md`** + `engine-seeds.md` (pipe, tu ne le réécris pas) + `team-generate.md` (`engine_ref=`).

`git pull origin master` ; branche **depuis `master`**.

Nouveau change OpenSpec **`core-5-seeds-fill`** (les deux moteurs dans **un** change). Skills → **propose puis apply**. Pas d’archive / sync. Pas de `/opsx-update` wellbeing-model (sauf si tu y touches fill / generate_team — alors **ce** change seulement).

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(core): core-5 seeds+core-2 fill and core-6 scarce recase`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés**. Seeds / SAT / budgets **inchangés**.

## Comportement

- Snapshot live `core-4` → `engines/core_4.py` (`engine.py` SHA `da1ef781ef572eb3eb30cde97060dd31788f79b5`). `data/bench/VERSION` → **`core-5`**. `list_engine_refs` = `core-0` … `core-6`. Live `engine.py` = `core-5`.
- **`core-5` fill** : remettre `int(not started_day)`. **Retirer** `int(creates_coupure)` et `coupure_matters`. Pipe seeds inchangé.
- **`core-6`** : module **nouveau** `engines/core_6.py` (pas un snapshot). Même pipe. Fill : rare → `int(not started_day)` ; sinon `int(creates_coupure)`. Rare = une fenêtre encore vide du cycle avec ≤ 3 légaux dont lui (`engine-core-6.md`).
- `generate_for` : `core-3`/`core-4`/`core-6` → `result.trace` réelle (pas le stub empty). `core-5` = live.
- `generate_team(..., engine_ref=)` omis = VERSION ; sinon `generate_for`. `UnknownEngineRef` si inconnu.

## Tests

`engine_ref() == "core-5"`. `list_engine_refs() == core-0…core-6`.  
Deux légaux, un déjà posé : `core-5` préfère le déjà-là.  
`core-6` : fenêtre large → pénalise la coupure ; rare déjà posé → préféré.  
`run_bench(tight, halles, minimal)` + `engine_ref="core-4"|"core-6"` verts. 50 listings. Pytest moteur verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core core-5+6 pushed @ <sha>`
