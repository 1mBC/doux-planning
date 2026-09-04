# Auth + rattachement employé

Freeze pour l’inscription / login / QR. Un compte = une entreprise. Un restaurateur par entreprise. Email unique global. Pas de mot de passe oublié en v1.  
`GET /v1/examples/saint-cloud` reste **public**, sans session.

Python Core (`employee-invite-tokens`) : code **entreprise** (`RestaurantIdentity.invite_code`) + **jeton employé** par fiche (`Employee.invite_token`). Infra wrappe, ne réinvente pas le redeem.

## Codes

| Nom | Portée | Usage |
|---|---|---|
| `company_code` | entreprise | inscription employé à la main + QR |
| `employee_token` | une fiche pas encore liée | QR : préremplit la fiche ; régénérable (l’ancien meurt) |

`employee_token` ≠ `employee_id`. Pas d’id brut dans le QR.

Redeem entreprise seul + `employee_id` (liste des fiches non liées) **ou** entreprise + `employee_token` (QR). Jeton déjà lié / inconnu / code entreprise faux → erreur.

## Routes publiques (Infra, après Core)

```
POST /v1/auth/register          { kind: "company"|"employee", email, password, company_code?, employee_token?, employee_id? }
POST /v1/auth/login             { email, password }
POST /v1/auth/logout            Bearer
GET  /v1/me                     Bearer
GET  /v1/invites/{company_code}  → { restaurant_name, employees: [{ id, name, role, team }] }  # fiches non liées seulement
```

QR web : `/register?company_code=…&employee_token=…` (même formulaire).  
Login : un seul écran, le `kind` vient de `GET /v1/me`.

Restaurateur : `POST /v1/staff/{id}/invite-token` régénère le jeton (Bearer resto).  
Inscription `kind: company` : email + password seulement (nom d’entreprise = panneau contexte, plus tard).

## Hors de ce freeze Core

Panneaux contexte, deux cycles, generate, persist live, hash Argon2, tables sessions. Core ne fait **que** les jetons / redeem dans `invites.py` + `Employee`.
