# Brief — coller dans le chat **UI**

Le tech lead : **Mode édition** sur `/planning` (sandbox live). Infra a fini `/v1/live/sandbox/{team}/…` (`live/infra`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-live-sandbox.md` + shapes `contracts/http/v1-sandbox-edit.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/live/infra` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`live/ui` depuis `master`**. **Ne merge pas** `live/infra` / `live/core`. API à part (proxy `/v1` inchangé).

`/opsx-update` **`build-planning-ui`**. Pas de mega-change. **Ne pas** changer le joujou `/exemple` (`/v1/sandbox/*` sans Bearer). Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.10.0`**, note FR sur l’édition du planning publié.

## Écrans

- `/planning` company, **seulement** si `published[team]` existe : bouton **Mode édition** → `POST /v1/live/sandbox/{team}/enter` (Bearer). Cuisine sans cycle : pas d’édition (409). Salarié : toujours hors `/planning`.
- En édition : même UX que le joujou — overlay occupé (retune ±15 **Valider**, replace, swap) + fill case vide, `detail` API, historique + **Annuler** + **Tout annuler** (`discard`). **Lecture** quitte l’UI d’édition **sans** discard (brouillon persisté ; reload `GET` live).
- **Publier** → `POST .../publish` → sortir d’édition, grille = `published` mis à jour (`GET /v1/cycles`). L’autre équipe intacte.
- Client live **distinct** : `/v1/live/sandbox/{team}/…` + Bearer. **Zéro** appel `/v1/sandbox/*` depuis `/planning`. Réutiliser parseurs / overlays existants (pas de nouveau score UI).
- `/exemple` + Mode édition joujou inchangés. Calculer / wizard inchangés.
- Types = contrat (`team` sur LiveState) ; clé manquante → throw. Pas de nouvelle dépendance.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Company salle calculée → Mode édition → retune Valider → cellule change → Lecture → Mode édition garde le cran → Publier → reload = publié. `/exemple` enter sandbox sans session toujours OK, 92. Barre `v0.10.0`.

Tâches cochées → stop.
