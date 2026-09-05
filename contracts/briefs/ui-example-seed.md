# Brief — coller dans le chat **UI**

Le tech lead : bouton **intégrer l’exemple** (pré-BETA, tous les comptes company). Infra a poussé **`origin/seed/infra` @ `71c9776`**. Relis `contracts/http/v1-context.md` (`POST /v1/context/seed-example`) et `contracts/domain/example-seed.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/seed/infra` ≠ `71c97767320fa7d9d67a354550a9459c87db23fd` → **stop**, remonte.  
`git pull origin master` ; branche **`seed/ui` depuis `master`**. **Ne merge pas** `seed/infra` / `seed/core`. API à part : uvicorn Infra @ `71c9776`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.13.0`**, note FR sur le bouton exemple.

## Écran

`/context` company **uniquement** (bandeau « Mon restaurant », à côté du code entreprise). **Tous** les comptes restaurateur — vide ou déjà rempli.

Bouton : **Intégrer l’exemple Saint-Cloud**.  
Avant le POST : confirm FR d’une phrase — ça **remplace** rôles, équipe, souhaits, types, semaine ; **garde le nom** ; **casse** les comptes salariés liés ; **ne** colle **pas** le planning exemple.

`POST /v1/context/seed-example` Bearer, **pas de body**. 200 = remplacer le state wizard (même parse que GET). `detail` si erreur. Busy pendant l’appel.

Après succès : salle **prête** (onglets débloqués), cuisine pas prête, fiches exemple, `week_labels` `"ab"`, nom inchangé. Pas de generate, pas d’aller sur `/planning` tout seul.

Pas de bouton côté salarié, `/exemple`, `/planning`, login.

Types TS = contrat. Pas de nouvelle dépendance.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Company vide → bouton → confirm → POST → Équipe montre Diane/Théo/…, semaine type remplie, badge salle prêt. Reload = persisté. 2ᵉ clic réécrase. Exemple public 92 sans session. Barre **v0.13.0**.

Tâches cochées → stop.  
Signal : `UI seed done, v0.13.0, no commit.`
