# Brief — coller dans le chat **Core Engine**

Le tech lead : **gate merge.** `git fetch origin` ; reste sur **`seed/core`** (base `777e8c5`). `git pull origin master` si master a avancé ; merge `origin/master` si besoin (pas de rebase force).

**Commit + push `seed/core`.** Message : `feat(core): seed_example_context from Saint-Cloud`. Un commit (OpenSpec + domaine ensemble OK). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher le seed. **Ne pas** toucher `api/` / `web/` / `contracts/` / `saint-cloud.json`.

119 verts inchangés → push → stop.  
Signal : `Core seed pushed @ <sha>`
