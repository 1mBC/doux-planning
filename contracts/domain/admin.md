# Admin (promote + log generate + moteur client)

Freeze **Infra** + **UI**.  
Pas de `kind: admin` au register. Pas de 2ᵉ compte à chaque deploy.  
Un seul `live_engine_ref` **global** (tous les restos clients). Pas un choix par restaurant.

## Promote

Env **`ADMIN_EMAIL`** (prod : `bastien.caujolle@gmail.com`).  
Au boot (après Alembic / seed), si un compte **restaurateur** existe avec cet email (minuscules) : `is_admin = true`. **Idempotent**.  

- Email absent en base → **ne rien créer**.
- `ADMIN_EMAIL` vide / unset → skip.
- Employé avec le même email → **ne pas** promouvoir (admin = restaurateur seulement).

`GET /v1/me` company : ajouter `admin: true|false`. Employee : `admin: false`.  
`kind` reste `"company"` | `"employee"`.

## Moteur client (`live_engine_ref`)

C’est le `engine_ref` lancé quand un **restaurateur** (pas l’admin banc) fait `POST /v1/generate` (sync **et** worker).  
Le banc ignore cette valeur (lancer habituel = `VERSION`).

Persist : **une** ligne (table dédiée ou settings). `engine_ref` text. Alembic oui.  
Unset / row absente → traiter comme `VERSION`.  
Si la valeur stockée **n’est plus** dans `list_engine_refs()` → traiter comme `VERSION` (ne **pas** 500 sur un generate client).

```
GET /v1/admin/live-engine   Bearer admin → 200
PUT /v1/admin/live-engine   Bearer admin → 200
```

200 :

```
{ engine_ref: "core-5", engine_refs: ["core-0","core-1","core-2","core-3","core-4","core-5","core-6"] }
```

`engine_refs` = `list_engine_refs()` (ordre registre).  
`engine_ref` = valeur **effective** (stockée si connue, sinon `VERSION`).

PUT body : `{ "engine_ref": "core-6" }`. Inconnu / vide / type faux → 400 `Moteur inconnu.`  
Non-admin → 403 `Action réservée à l’admin.` Sans session 401. Sans DB 503.

`generate_team(..., engine_ref=effective)` à chaque generate 200 / job done. Body POST generate **inchangé**.

## Log generate

Uniquement **`POST /v1/generate` 200** / job `done`. Pas 409, pas seed, pas import, pas publish sandbox.

Ligne :

```
{ created_at, email, restaurant_name, team, search_effort, duration_seconds, engine_ref, facts[] }
```

`email` = compte company. `restaurant_name` = `companies.name` au moment du solve.  
`search_effort` = celui du POST / job.  
`duration_seconds` = temps wall-clock du solve (float, ≥ 0).  
`engine_ref` = le moteur **réellement** lancé (effective).  
`facts` = **misses evaluate** du cycle venant d’être généré (`polarity: miss`, `kind != role_gap`) — forme `score-facts.md` **plus** `employee_name` (nom fiche au moment du log, `null` si pas d’id).  
Colonne JSONB existante : dual-read `warnings` → `facts` à la lecture. Nouvelles écritures = `facts` (pas de `message`).  
Table `generate_logs`. Newest-first. Vieux rows : `search_effort` / `duration_seconds` / `engine_ref` **null**.

## `GET /v1/admin/generates`

Bearer. `admin !== true` → 403 `Action réservée à l’admin.`  
200 : `{ entries: [ { id, created_at ISO, email, restaurant_name, team, search_effort, duration_seconds, engine_ref, facts } ] }` **plus récent d’abord**.  
GET n’exige plus `warnings`. Vieux row `warnings[]` avec `message` : hydrater en facts (`kind = code`, `payload = {}`) **et** laisser `message` sur cet item seulement (`score-facts.md` Hydrate).  
Sans session 401. Sans DB 503.

## UI — `/admin`

Company **`me.admin === true` seulement**. Pas salarié, pas `/exemple`, pas `/planning`.  
Lien **Admin** dans le chrome session **ssi** `me.admin`. Sinon : pas de lien ; `/admin` tapé à la main → message `Action réservée à l’admin.` (pas d’appel API).

`parseMe` **lit** `admin: bool`. Employee : toujours `false`.

**Sélecteur** en haut de `/admin` (historique), **avant** la table :

- Libellé **« Moteur du planning client »**.
- Sous-texte : « C’est ce modèle qui tourne quand un restaurateur calcule son planning. Le banc n’est pas affecté. »
- `<select>` = `engine_refs` (ids tels quels : `core-5`). Valeur = `engine_ref` du GET.
- Changement → PUT immédiat, puis le select affiche la 200.
- `GET /v1/admin/live-engine` au chargement (en plus des generates). Échec GET → message `detail`, select désactivé.

`GET /v1/admin/generates` Bearer au chargement. Vide → « Aucun generate pour l’instant. » (le sélecteur **reste**).

Table **newest-first** (ordre API). **En-tête par jour calendaire** `Europe/Paris` (`created_at`) : `Dimanche 6 septembre 2026`. Un bloc par jour qui a au moins une ligne ; pas de jour vide. Dans le bloc : heure `HH:mm` Paris, email, nom resto, équipe, **effort** (Minimal / Optimisé / Maximal, tiret si null), **durée** (`Ns` / `N min`, tiret si null), **moteur** (`engine_ref`, tiret si null), pastille **N misses**.

**Hover** = une carte par fact, **dictionnaire `score-facts.md`** : gravité, titre kind, jour + semaine, personne (`employee_name`), gabarit payload. Vieux row sans payload : `message` en dernier recours. `[]` → `aucun warning`. Champs absents → tiret.

Company `/planning` : ligne date/heure + modèle = `generate-versions.md`. **Pas** de sélecteur moteur sur `/planning`.

SPA fallback `/admin` (Railway déjà `index.html` pour `/planning`, `/login`). **Pas** de nouvelle route SPA. Routes HTTP admin ci-dessus **oui**.

## Hors freeze

Banc + **Versions** = `contracts/domain/bench.md`. Un moteur **par** resto. Supprimer un salarié / panneau compte. Archive / sync.
