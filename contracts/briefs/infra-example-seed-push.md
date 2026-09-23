# Brief — coller dans le chat **Infra**

Le tech lead : **gate merge.** `git fetch origin` ; reste sur **`seed/infra`** (HEAD = merge Core `bb9ac1d`). `git pull origin master` si master a avancé ; merge `origin/master` si besoin (pas de rebase force).

**Commit + push `seed/infra`.** Message : `feat(api): POST /v1/context/seed-example`. Un commit (OpenSpec + `api/` ensemble OK). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher le wrap. **Ne pas** toucher `web/` / `contracts/` / `context.py` Core / `saint-cloud.json`.

132 verts inchangés → push → stop.  
Signal : `Infra seed pushed @ <sha>`
