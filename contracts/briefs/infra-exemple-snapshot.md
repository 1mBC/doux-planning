# Brief — coller dans le chat **Infra**

Le tech lead : **merge + dual-read**. Core a poussé **`origin/snapshot/core` @ `609dd30`**. Landé sur master @ **`e046338`**. Snapshot : 92 / warnings **17** / wellbeing **10/12** ; wish live ; messages FR. Relis `contracts/domain/exemple-snapshot.md` et `contracts/http/v1-examples.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/snapshot/core` ≠ `609dd3043f167c5c5ef7e372ce1291fa14bb6629` → **stop**, remonte.  
`git pull origin master` (plus récent que `e046338`, doit contenir ce brief) ; branche **`snapshot/infra` depuis `master`** ; merge **`origin/snapshot/core`** (déjà dans master — ne pas réécrire le JSON).

**Pas** de `/opsx-update` exemple-snapshot / warn-fr / seed / sandbox. Pas d’archive / sync. **Pas** de nouvelle route, **pas** d’Alembic. **Pas** de `generate_cycle` sur GET exemple.

**Process** : pytest vert → **commit + push `snapshot/infra` toi-même**. Message : `feat(api): serve refreshed saint-cloud snapshot`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `contracts/`, `engine.py`, `saint-cloud.json` (Core l’a déjà réécrit). Si un test HTTP pin `we1j` / message EN : **aligne** sur 92 / 17 / 10/12 / wish live / FR.

## Comportement

`GET /v1/examples/saint-cloud` (fichier **et** Postgres après `seed_from_files`) = nouveau `planning` : 92, 17 warnings FR, wellbeing 10/12, plus de `we1j`. Seed boot **rafraîchit** `example_snapshots.planning` depuis le fichier (déjà le cas — vérifier, ne pas inventer un 2ᵉ seed). Cuisine `null` / generate live inchangés.

## Tests

Pytest api : exemple 92 sans session ; dual-read `DATABASE_URL` = mêmes 92 / 17 / 10/12 ; un warning `contrat` FR ; `wish_cols` sans `we1j`. Auth / context / generate verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra snapshot pushed @ <sha>`
