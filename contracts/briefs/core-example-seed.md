# Brief — coller dans le chat **Core Engine**

Le tech lead : seed exemple → contexte live. Relis `contracts/domain/example-seed.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; master doit avoir **`11dc586`** (`master has wellbeing landed`) ou plus récent. Branche **`seed/core` depuis `master`**. Pas `wellbeing/core`.

Nouveau change OpenSpec **`example-seed`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` wellbeing / sandbox / generate. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. Pas de `hydrate_delivered_cycle` (cycle + sandbox). Ne pas réécrire `saint-cloud.json`.

## Comportement

- `seed_example_context(state)` selon le freeze. Mapping structures → types + semaine + échelles. Tokens neufs. Published / live / cycle vidés. Nom + id + légal **gardés**.

## Tests

Scénarios du freeze + pytest domaine verts.

Tâches cochées + pytest vert → stop.  
Signal : `Core seed done, pytest <n> passed, no commit.`
