# Brief — coller dans le chat **Infra**

Le tech lead : slice auth HTTP. Core a fini les jetons (`auth/core`, pytest vert, pas encore de commit tant que le facteur ne l’a pas demandé). Relis `contracts/http/v1-auth.md` (tu le suis, tu ne le modifies pas). `git fetch origin` ; si `origin/auth/core` manque → **stop**, remonte au facteur. Sinon : branche **`auth/infra` depuis `master`**, merge **`origin/auth/core`** (Python hors `api/` uniquement — ne pas réécrire ce merge).

`/opsx-update` le change existant **`build-planning-api`** (section 2 seulement) pour aligner les routes **unifiées** du contrat. Les chemins `/v1/auth/restaurateur/*` et `/v1/auth/employee/*` du vieux design **ne s’implémentent pas**. Pas de nouveau mega-change. Pas de `/opsx-update` sandbox. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `contracts/`, `planning.py`, `engine.py`, `invites.py`, `staff.py`, `hydrate.py`, preview/fill, generate, jobs. Reste dans `src/doux_planning/api/` + Alembic + Compose + `pyproject.toml` (Argon2) + tests TestClient.

## Comportement

- `POST /v1/auth/register` `{ kind, email, password, company_code?, employee_token?, employee_id? }` → 201 `{ token, me }`.
  - `kind: company` : email+password, **nouvelle** entreprise vide (`name` `""`), un restaurateur. Pas Saint-Cloud.
  - `kind: employee` : wrappe `redeem_invite` (QR ou manuel). Fiche déjà liée / mauvais code → erreurs du contrat.
- `POST /v1/auth/login` `{ email, password }` → 200 `{ token, me }`. Un seul login ; `kind` vient de `me`.
- `POST /v1/auth/logout` Bearer → 204, jeton mort.
- `GET /v1/me` Bearer → 200 `me` (`kind` `"company"`|`"employee"`, `employee_id` null si company).
- `GET /v1/invites/{company_code}` public → fiches **non** liées seulement (`linked_employee_ids`). Pas de token dans le JSON.
- `POST /v1/staff/{id}/invite-token` Bearer company → `rotate_employee_invite_token`, renvoie le nouveau token une fois.
- Argon2 + sessions hashées. Email unique global. Dual-read : sans `DATABASE_URL`, exemple public inchangé ; auth → 503.
- **Sandbox inchangé / public.** Pas de persist panneaux, pas de generate.

## Tests (TestClient)

Register company → login → `/me` kind company ; second email → 409 ; mauvais password → 401 ; logout puis `/me` → 401.  
Insérer deux fiches test ; `GET /invites` les voit ; register employee manuel sur A → 201 + plus dans invites ; même fiche → 409 ; QR token B → lie B ; mauvais `company_code` → 400. Rotate A : ancien token refuse, nouveau OK.  
`GET /v1/examples/saint-cloud` toujours 200 / 92 assignments, avec et sans session. Routes sandbox existantes toujours 200 sans Bearer.

Tâches section 2 cochées + pytest vert → stop.
