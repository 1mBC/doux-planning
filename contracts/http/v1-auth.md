# Auth + rattachement employé

Freeze HTTP pour inscription / login / QR / session.  
Un compte = une entreprise. Un restaurateur par entreprise (un `kind: company` crée **une nouvelle** entreprise, pas un second patron sur Saint-Cloud). Email unique **global**. Pas de mot de passe oublié en v1.

`GET /v1/examples/saint-cloud` reste **public**, sans session, dual-read inchangé (`contracts/http/v1-examples.md`).  
Les routes `/v1/sandbox/*` restent **publiques** dans cette tranche (l’UI auth n’est pas livrée). Ne pas les verrouiller ici.

Python Core (`employee-invite-tokens` sur `auth/core`) : wrappe `redeem_invite`, `rotate_employee_invite_token`, `RestaurantIdentity.invite_code` / `linked_employee_ids`, `Employee.invite_token`. Ne pas réinventer le redeem.

Les vieilles routes OpenSpec `/v1/auth/restaurateur/*` et `/v1/auth/employee/*` **ne s’implémentent pas**. Ce fichier gagne.

## Codes

| Nom | Portée | Usage |
|---|---|---|
| `company_code` | entreprise | inscription employé à la main + QR + `GET /v1/invites/{company_code}` |
| `employee_token` | une fiche pas encore liée | QR : préremplit la fiche ; régénérable (l’ancien meurt) |

`employee_token` ≠ `employee_id`. Pas d’id brut dans le QR.  
`kind` JSON : `"company"` | `"employee"` (jamais `"restaurateur"`).

## Session

`Authorization: Bearer <token>` — jeton opaque, renvoyé **une fois** au register/login. Persister uniquement un hash. Argon2 pour les mots de passe. Pas de JWT, pas de cookie requis.

Corps session (register + login) :

```
{ "token": "<opaque>", "me": { "kind": "company"|"employee", "email": "...", "restaurant_id": "...", "employee_id": null|"..." } }
```

`GET /v1/me` = l’objet `me` (sans `token`).  
`kind: company` → `employee_id` est `null`.  
`kind: employee` → `employee_id` = id de fiche.

## Routes

```
POST /v1/auth/register          → 201 { token, me }
POST /v1/auth/login             → 200 { token, me }
POST /v1/auth/logout            → 204   (Bearer)
GET  /v1/me                     → 200 me (Bearer)
GET  /v1/invites/{company_code} → 200 { restaurant_name, employees: [{ id, name, role, team }] }
POST /v1/staff/{id}/invite-token → 200 { employee_id, employee_token }  (Bearer company)
```

QR web (UI plus tard) : `/register?company_code=…&employee_token=…`. Infra ne sert pas cette page.

### `POST /v1/auth/register`

```
{ "kind": "company"|"employee", "email": "...", "password": "...",
  "company_code": "...?", "employee_token": "...?", "employee_id": "...?" }
```

- `kind: company` : **email + password seulement**. Créer une entreprise vide (nom `""` jusqu’au panneau contexte). Ignorer / 400 si `company_code`, `employee_token` ou `employee_id` sont envoyés. Ne **pas** attacher le compte au resto d’exemple Saint-Cloud.
- `kind: employee` : `company_code` obligatoire, plus **QR** (`employee_token`) **ou** **manuel** (`employee_id`). Les deux fournis → passer au Core (token gagne ; id qui ne matche pas → erreur Core).
- Mot de passe : ≥ 8 caractères.
- Succès : 201 + session (connecté tout de suite).

### `POST /v1/auth/login`

```
{ "email": "...", "password": "..." }
```

Un seul écran. Le `kind` sort de `me`. 200 + session.

### `POST /v1/auth/logout`

Bearer. 204. Jeton invalidé. Second logout / jeton inconnu → 401.

### `GET /v1/me`

Bearer. 200 = `me`. Sans / mauvais jeton → 401.

### `GET /v1/invites/{company_code}`

Public. 200 : `restaurant_name` (souvent `""`), `employees` = fiches **non** dans `linked_employee_ids` seulement.  
Chaque employé : `id`, `name`, `role` (string = nom de poste), `team` (`"salle"` | `"cuisine"`).  
Ne jamais renvoyer `invite_token`, email, hash.  
Code inconnu → 404.

### `POST /v1/staff/{id}/invite-token`

Bearer **company**. Appelle `rotate_employee_invite_token`. 200 : nouveau `employee_token` (une fois).  
Employé → 403. Fiche d’une autre entreprise / inconnue → 404.

## Erreurs (nouveaux endpoints)

Même forme que le sandbox : `{ "detail": "<français>" }`.

| Cas | HTTP | `detail` |
|---|---|---|
| Champs manquants / kind inconnu / password < 8 / company avec champs employé | 400 | `Champs invalides.` |
| `InvalidInviteCode` / jeton inconnu | 400 | `Code entreprise ou jeton invalide.` |
| Email ou mot de passe faux | 401 | `Email ou mot de passe incorrect.` |
| Session absente / invalide / déjà logout | 401 | `Session invalide.` |
| Employé sur route restaurateur | 403 | `Action réservée au restaurateur.` |
| Email déjà pris | 409 | `Cet email est déjà utilisé.` |
| Fiche déjà liée | 409 | `Cette fiche a déjà un compte.` |
| `company_code` inconnu (`GET /invites`) | 404 | `Entreprise introuvable.` |
| Fiche inconnue (rotate) | 404 | `Fiche introuvable.` |
| Auth sans `DATABASE_URL` | 503 | `Base indisponible.` |

## Persist (Infra)

Nouvelles tables (ne pas réutiliser la ligne `restaurants` / snapshot Saint-Cloud pour un register `company`) :

- entreprise live : id, `invite_code`, `name` (`""`), `linked_employee_ids`
- fiches live : id, company_id, name, role, team, `invite_token` (pour invites + redeem ; pas de CRUD staff public dans cette tranche — les tests insèrent des fiches)
- `restaurateur_accounts` / `employee_accounts` (email unique global, hash Argon2)
- `sessions` (hash du token, kind, account_id, restaurant_id, expires_at)

Register `company` : `RestaurantIdentity(...)` Core → persister `invite_code`.  
Register `employee` : charger l’identité + fiches, `redeem_invite`, persister compte + `linked_employee_ids`.  
Ne pas écrire `data/examples/saint-cloud.json` ni `example_snapshots`.

## Hors de cette tranche

Panneaux contexte, deux cycles, generate, persist staff/hours UI, `/me/shifts`, jobs, verrouillage sandbox, CORS sauf si le proxy Vite casse. Core ne se retouche pas (`invites.py` / `staff.py` / `hydrate.py`).
