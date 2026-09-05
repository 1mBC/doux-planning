# Brief — coller dans le chat **Core Engine**

Le tech lead : **gate merge.** Relis `contracts/http/v1-examples.md` (stats snapshot **à jour** sur master). `git pull origin master` (contrat exemple) ; reste sur **`wellbeing/core`**. Merge `origin/master` si besoin (pas de rebase force).

**Commit + push `wellbeing/core`.** Message : `feat(core): wellbeing model and Saint-Cloud snapshot`. Un commit (ou 2 si OpenSpec / JSON déjà séparés — pas de squash ensuite). Pas de PR master. Pas d’archive / sync.

Ne pas retoucher le moteur. **Ne pas** patcher `api/` / `web/` / `contracts/`. Les 4 ImportError HTTP restent pour Infra.

Tâches OpenSpec déjà cochées + 113 verts inchangés → push → stop.  
Signal : `Core wellbeing pushed @ <sha>`
