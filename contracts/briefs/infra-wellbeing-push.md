# Brief — coller dans le chat **Infra**

Le tech lead : **gate merge.** `git fetch origin` ; reste sur **`wellbeing/infra`** (HEAD = merge Core `4005994`). `git pull origin master` si master a avancé ; merge `origin/master` si besoin (pas de rebase force).

**Commit + push `wellbeing/infra`.** Message : `feat(api): wellbeing HTTP object and week_labels`. Un commit (OpenSpec + `api/` ensemble OK). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher le wrap. **Ne pas** toucher `web/` / `contracts/` / moteur / `saint-cloud.json`.

128 verts inchangés → push → stop.  
Signal : `Infra wellbeing pushed @ <sha>`
