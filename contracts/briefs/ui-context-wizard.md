# Brief — coller dans le chat **UI**

Le tech lead : wizard contexte (rôles → fiches → services → types → semaine). Infra a fini `GET`/`PATCH /v1/context` (`context/infra`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-context.md` et `contracts/domain/restaurant-context.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/context/infra` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`context/ui` depuis `master`**. **Ne merge pas** `context/infra` / `context/core`. API à part (proxy `/v1` inchangé).

`/opsx-update` **`build-planning-ui`**. Pas de mega-change, pas de `/opsx-update` sandbox, pas d’archive / sync, pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.8.0`**, note FR sur le wizard contexte.

## Écrans

- `kind: company` : route **`/context`**. Après login/register entreprise, y aller (lien chrome « Mon restaurant »). Salarié : **pas** de wizard (403 API) — exemple + phrase planning plus tard, comme aujourd’hui.
- Sans session : login / register / **Voir l’exemple** inchangés. Ne pas exiger Postgres pour l’exemple.
- Bandeau identité : nom resto (PATCH `name`, `""` OK) + « Droit du travail : France » **lecture seule** (`legal_context_id`, pas de règles copiées) + `company_code` affiché.
- Wizard **séquentiel** puis tout reste éditable. Salle et cuisine **indépendantes** (on peut finir la salle seule).
  1. **Rôles** (par équipe) : nom + niveau ≥ 1. Afficher la règle : un niveau plus élevé peut tenir un poste inférieur. PATCH `ladders` avec `substitution_explained: true`.
  2. **Fiches** (par équipe) : nom, rôle de l’échelle, heures contrat, indispos (jour / matin / soir / service), souhaits wellbeing (clés du contrat), `min_shift_hours` défaut **4**. PATCH `employees` = **liste complète** (ne pas oublier l’autre équipe). Afficher `invite_token` + URL `/register?company_code=…&employee_token=…`. Pas de rotate (déjà `POST /v1/staff/{id}/invite-token` plus tard).
  3. **Services** (entreprise, une fois) : petit-déj / déj / dîner → `morning` / `midday` / `evening`. PATCH `services`.
  4. **Types** (équipe × service) : feuille nommée, vagues arrivée/départ, heures ±15 min, `post_levels`. PATCH `types` = **liste complète** (garder les types de l’autre équipe).
  5. **Semaine type** (lun–dim × services) : type ou **Fermé**, par équipe. PATCH `typical_week` remplace `{ salle, cuisine }` : renvoyer **les deux** clés. Cellule fermée : `closed: true`, `type_id` null.
- `ready.salle` / `ready.cuisine` : **uniquement** le JSON, badges FR « Prêt à calculer » / « Pas encore prêt ». **Aucun** bouton generate, aucun `generate_cycle`.
- Bearer sur `GET`/`PATCH /v1/context` seulement (plus auth déjà en place). Toujours pas sur exemple / sandbox.
- Types TS = contrat ; clé manquante → throw. Afficher `detail` API. Pas de nouvelle dépendance.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Company : nom + 5 étapes salle jusqu’à `ready.salle` true / cuisine false. Reload = même contexte. Salarié n’ouvre pas `/context`. Exemple 92 sans session. Barre `v0.8.0`.

Tâches cochées → stop.
