# Admin (promote + log generate)

Freeze **Infra**. Table UI = brief UI ensuite.  
Pas de `kind: admin` au register. Pas de 2ᵉ compte à chaque deploy.

## Promote

Env **`ADMIN_EMAIL`** (prod : `bastien.caujolle@gmail.com`).  
Au boot (après Alembic / seed), si un compte **restaurateur** existe avec cet email (minuscules) : `is_admin = true`. **Idempotent**.  

- Email absent en base → **ne rien créer**.
- `ADMIN_EMAIL` vide / unset → skip.
- Employé avec le même email → **ne pas** promouvoir (admin = restaurateur seulement).

`GET /v1/me` company : ajouter `admin: true|false`. Employee : `admin: false`.  
`kind` reste `"company"` | `"employee"`.

## Log generate

Uniquement **`POST /v1/generate` 200**. Pas 409, pas seed, pas import, pas publish sandbox.

Ligne :

```
{ created_at, email, restaurant_name, team, warnings[] }
```

`email` = compte company. `restaurant_name` = `companies.name` au moment du solve. `warnings` = array du cycle **venant d’être** généré (même forme HTTP).  
Table `generate_logs` (Alembic). Newest-first à la lecture.

## `GET /v1/admin/generates`

Bearer. `admin !== true` → 403 `Action réservée à l’admin.`  
200 : `{ entries: [ { id, created_at ISO, email, restaurant_name, team, warnings } ] }` **plus récent d’abord**.  
Sans session 401. Sans DB 503.

## Hors freeze

Table UI (en-têtes par jour, hover warnings), coerce Railway, archive / sync.
