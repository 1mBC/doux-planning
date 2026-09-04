# Brief — coller dans le chat **UI**

Le tech lead : slice écrans auth. Infra a fini le HTTP (`auth/infra`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-auth.md` (tu le suis, tu ne le modifies pas). `git fetch origin` ; si `origin/auth/infra` manque → **stop**, remonte au facteur. Sinon : `git pull origin master` ; branche **`auth/ui` depuis `master`**. **Ne merge pas** `auth/infra` / `auth/core` (Python). L’API tourne à part (proxy Vite `/v1` inchangé).

`/opsx-update` le change existant **`build-planning-ui`** pour les écrans login/register. Pas de nouveau mega-change. Pas de `/opsx-update` sandbox. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste dans `web/`. Incrémente `web/src/release.ts` + `web/package.json` (`0.7.0`, note FR sur connexion / inscription).

## Écrans

- **Un** login : email + mot de passe → `POST /v1/auth/login`. Le `kind` vient de `me`, pas d’un sélecteur.
- **Un** register (`/register`) : bascule **Entreprise** / **Salarié** (pas « restaurateur »).
  - Entreprise : email + password seulement → `kind: company`. Pas de nom d’entreprise.
  - Salarié : code entreprise → `GET /v1/invites/{company_code}` → choisir une fiche (`id`, name, role, team) → email + password → `kind: employee` + `employee_id`. Pas de token dans le POST sauf QR.
- QR : **même** register, query `company_code` + `employee_token`. Kind salarié verrouillé, pas de liste de fiches, POST avec `employee_token` (pas d’`employee_id`).
- Pas de « mot de passe oublié ». Password ≥ 8. Afficher `detail` API tel quel.
- Token : `sessionStorage`, header `Authorization: Bearer` sur register/login/logout/`/me`. **Pas** sur `/v1/examples/*` ni `/v1/sandbox/*`.
- Session : email + kind (Entreprise / Salarié) + **Déconnexion** (`POST /v1/auth/logout`, oublier le token). Reload : `GET /v1/me` ; 401 → login.
- Sans session : les écrans auth **et** l’exemple Saint-Cloud restent accessibles (lien « Voir l’exemple »). Ne pas bloquer la grille derrière le login — sans `DATABASE_URL` l’auth est 503, l’exemple doit encore marcher.
- `kind: employee` : **pas** de Mode édition. Phrase FR : le planning publié personnel arrive plus tard.
- `kind: company` : grille + sandbox comme aujourd’hui (joujou public).
- **Hors slice** : rotate invite-token, panneaux contexte, wizard équipes, grille employé colorée, generate.

Pas de nouvelle dépendance (pas de react-router si `pathname` + `URLSearchParams` suffisent). Types = JSON du contrat ; clé manquante → throw, ne pas inventer.

## Vérif (IronBee DevTools, pas le browser Cursor)

`npm run build`. Login company → `/me` → Déconnexion. Register employee manuel (fiches via API/invites) + QR query. Exemple 92 assignments sans session. Employee : pas de Mode édition. Barre `v0.7.0` + note.

Tâches cochées → stop.
