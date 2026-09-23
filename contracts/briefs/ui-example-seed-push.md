# Brief — coller dans le chat **UI**

Le tech lead : **gate merge.** `git fetch origin` ; reste sur **`seed/ui`** (base `0764a88`, pas de merge Python). `git pull origin master` si master a avancé ; merge `origin/master` si besoin (pas de rebase force).

**Commit + push `seed/ui`.** Message : `feat(web): seed example button v0.13.0`. Un commit (`web/` + OpenSpec UI ensemble OK). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher les écrans. **Ne pas** toucher `src/doux_planning/` / `contracts/`.

`npm run build` inchangé → push → stop.  
Signal : `UI seed pushed @ <sha>`
