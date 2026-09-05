# Brief — coller dans le chat **UI**

Le tech lead : **gate merge.** `git fetch origin` ; reste sur **`wellbeing/ui`** (base `8ba58e8`, pas de merge Python). `git pull origin master` si master a avancé ; merge `origin/master` si besoin (pas de rebase force).

**Commit + push `wellbeing/ui`.** Message : `feat(web): Equipe / Souhaits v0.12.0`. Un commit (`web/` + OpenSpec UI ensemble OK). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher les écrans. **Ne pas** toucher `src/doux_planning/` / `contracts/`. Pas de bouton seed.

`npm run build` inchangé → push → stop.  
Signal : `UI wellbeing pushed @ <sha>`
