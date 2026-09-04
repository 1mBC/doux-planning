# Brief — coller dans le chat **UI**

Le tech lead : bouton **Calculer** + grille du cycle publié. Infra a fini `POST /v1/generate` + `GET /v1/cycles` (`generate/infra`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-generate.md` (tu le suis, tu ne le modifies pas).

`git fetch origin` ; si `origin/generate/infra` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`generate/ui` depuis `master`**. **Ne merge pas** `generate/infra` / `generate/core`. API à part (proxy `/v1` inchangé).

`/opsx-update` **`build-planning-ui`**. Pas de mega-change, pas de `/opsx-update` sandbox. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.9.0`**, note FR sur Calculer / planning publié.

## Écrans

- `kind: company` : route **`/planning`**. Lien chrome « Planning ». Salarié : pas d’accès (403) — exemple + phrase plus tard.
- Au load : `GET /v1/cycles` + `GET /v1/context` (fiches pour la grille). Types = JSON ; clé manquante → throw.
- Sélecteur Salle / Cuisine. **Calculer** actif seulement si `ready[team] === true` (badge wizard / context, pas un bool inventé). Sinon bouton disabled, pas de POST.
- `POST /v1/generate` `{ team, search_effort: "minimal" }` — **minimal** dans cette tranche (optimized 30 s plus tard). Busy + `detail` si 409/400.
- 200 / GET : si `published[team]` non null, grille 14 j. (semaines A/B) comme l’exemple : fiches **de cette équipe** + `assignments` + liste `warnings` (message moteur, sévérité FR). **Pas** de `stats` / `legal_rows` / `wish_rows` inventés. **Pas** de Mode édition / sandbox sur ce cycle.
- Cuisine `null` alors que salle publiée : grille cuisine vide / « Pas encore calculé », salle intacte.
- Reload = même `GET /v1/cycles`. Recalculer remplace cette équipe.
- Bearer sur `/v1/generate` et `/v1/cycles` (plus context/auth). Jamais sur exemple / sandbox.
- Voir l’exemple + sandbox joujou inchangés. Wizard `/context` inchangé (badges ready restent).
- Pas de nouvelle dépendance.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Company salle ready → Calculer → cellules + warnings ; cuisine pas ready → bouton off / 409 si forcé. Reload garde la salle. Salarié hors `/planning`. Exemple 92 sans session. Barre `v0.9.0`.

Tâches cochées → stop.
