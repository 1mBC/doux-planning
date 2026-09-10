# Admin (promote + log generate)

Freeze **Infra** (landed `admin/infra`) + **UI** (table).  
Tranche 27 : log `search_effort` / `duration_seconds` / `employee_name` + hover recap.  
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
{ created_at, email, restaurant_name, team, search_effort, duration_seconds, facts[] }
```

`email` = compte company. `restaurant_name` = `companies.name` au moment du solve.  
`search_effort` = celui du POST / job.  
`duration_seconds` = temps wall-clock du solve (float, ≥ 0).  
`facts` = **misses evaluate** du cycle venant d’être généré (`polarity: miss`, `kind != role_gap`) — forme `score-facts.md` **plus** `employee_name` (nom fiche au moment du log, `null` si pas d’id).  
Colonne JSONB existante : dual-read `warnings` → `facts` à la lecture. Nouvelles écritures = `facts` (pas de `message`).  
Table `generate_logs`. Newest-first. Vieux rows : `search_effort` / `duration_seconds` **null**.

## `GET /v1/admin/generates`

Bearer. `admin !== true` → 403 `Action réservée à l’admin.`  
200 : `{ entries: [ { id, created_at ISO, email, restaurant_name, team, search_effort, duration_seconds, facts } ] }` **plus récent d’abord**.  
GET n’exige plus `warnings`. Vieux row `warnings[]` avec `message` : hydrater en facts (`kind = code`, `payload = {}`) **et** laisser `message` sur cet item seulement (`score-facts.md` Hydrate).  
Sans session 401. Sans DB 503.

## UI — table `/admin`

Company **`me.admin === true` seulement**. Pas salarié, pas `/exemple`, pas `/planning`.  
Lien **Admin** dans le chrome session **ssi** `me.admin`. Sinon : pas de lien ; `/admin` tapé à la main → message `Action réservée à l’admin.` (pas d’appel API).

`parseMe` **lit** `admin: bool` (aujourd’hui ignoré). Employee : toujours `false`.

`GET /v1/admin/generates` Bearer au chargement. Vide → « Aucun generate pour l’instant. »

Table **newest-first** (ordre API). **En-tête par jour calendaire** `Europe/Paris` (`created_at`) : `Dimanche 6 septembre 2026`. Un bloc par jour qui a au moins une ligne ; pas de jour vide. Dans le bloc : heure `HH:mm` Paris, email, nom resto, équipe, **effort** (Minimal / Optimisé / Maximal, tiret si null), **durée** (`Ns` / `N min`, tiret si null), pastille **N misses**.

**Hover** = une carte par fact, **dictionnaire `score-facts.md`** : gravité, titre kind, jour + semaine, personne (`employee_name`), gabarit payload. Vieux row sans payload : `message` en dernier recours. `[]` → `aucun warning`. Champs absents → tiret.

SPA fallback `/admin` (Railway déjà `index.html` pour `/planning`, `/login`). **Pas** de nouvelle route HTTP.

## Hors freeze

Banc + **Versions** = `contracts/domain/bench.md`. Supprimer un salarié / panneau compte. Archive / sync.
