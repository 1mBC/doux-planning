# Brief — coller dans le chat **UI**

Le tech lead : écran **salarié** — grille équipe + highlight + panneau contrat/souhaits. Infra a fini `GET /v1/me/planning` (`employee/infra`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-me-planning.md` (tu le suis, tu ne le modifies pas).

`git fetch origin` ; si `origin/employee/infra` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`employee/ui` depuis `master`**. **Ne merge pas** `employee/infra` / `employee/core`. API à part (proxy `/v1` inchangé).

`/opsx-update` **`build-planning-ui`**. Pas de mega-change. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.11.0`**, note FR sur le planning salarié.

## Écrans

- `kind: employee` : `/planning` (après login/register, lien chrome « Planning »). `GET /v1/me/planning` Bearer. **Pas** de Calculer, Mode édition, wizard, generate, live sandbox, context.
- Grille 14 j. (A/B) = `employees` + `assignments` de **son** équipe. Lignes `employee_id === me` **colorées** ; les collègues visibles mais atténués. Assignments vides → « Pas encore publié ».
- Panneau lecture : contrat (`weekly` / `assigned` / `ok`), indispos, souhaits (`key` → libellé FR, `held` tenu / non tenu). **Aucun** edit. Pas de `wish_rows` inventés.
- Company `/planning` / `/context` / live **inchangés**. `/exemple` joujou inchangé. Retirer « Le planning publié personnel arrive plus tard. »
- Types = contrat ; clé manquante → throw. `detail` API. Pas de nouvelle dépendance.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Salarié lié à une fiche salle publiée → `/planning` grille équipe, sa ligne en couleur, souhaits/contrat visibles. Company sur `/planning` garde Calculer. Exemple 92 sans session. Barre `v0.11.0`.

Tâches cochées → stop.
