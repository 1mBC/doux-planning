# Brief — coller dans le chat **Core Engine**

Le tech lead : **`core-4`**. Anti-coupure **seulement s’il y a le choix**. Relis **`contracts/domain/engine-core-4.md`** (gagne) + `engine-seeds.md` (pipe, tu ne le réécris pas).

`git pull origin master` ; branche **depuis `master`**.

Nouveau change OpenSpec **`core-4-coupure-choice`**. Skills → **propose puis apply**. Pas d’archive / sync. Pas de `/opsx-update` wellbeing-model.

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(core): core-4 coupure only when there is a choice`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Catalogue **50 jeux bit-à-bit**. Keep-best / `_attempt_key` **inchangés**. Seeds / SAT / budgets **inchangés**.

## Comportement

- Snapshot live `core-3` → `engines/core_3.py`. `data/bench/VERSION` → **`core-4`**. `list_engine_refs` = `core-0` … `core-4`. Live `engine.py` = `core-4`.
- Fill : **ne pas** remettre `int(not started_day)`.
- `_creates_coupure` inchangé. `max_coupures_per_week` skip inchangé.
- Parmi les légaux de **cette** fenêtre : s’il existe **au moins un** sans coupure → pénaliser `int(creates_coupure)` comme `core-3`. Sinon → composant coupure **0**, on couvre le poste.
- Phrase resto : on ne laisse pas un service à découvert pour protéger le confort d’une fiche s’il n’y a personne d’autre.

## Tests

`engine_ref() == "core-4"`.  
Deux légaux dont un sans coupure : le coupure est moins bien classé.  
Un seul légal « avec coupure » : **posé**.  
`run_bench(tight, halles, minimal)` vert. `engine_ref="core-3"` joue le snapshot. 50 listings. Pytest moteur verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core core-4 pushed @ <sha>`
