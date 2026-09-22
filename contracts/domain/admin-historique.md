# Historique admin — note, voir, se connecter (file 70)

Freeze **Infra + UI**. **Pas de Core.**  
Gagne sur `admin.md` (log generate + table `/admin`) et `v1-auth.md` (session) pour ces trois gestes.  
Lots 71–72 = `bench-import.md` / `bench-chrome.md` — **hors ce file**.

Trois gestes sur **Historique des computes** (`/admin`) :

1. **Note** = `score.global` **/10** de **ce** generate (pas le latest du resto).
2. **Voir le planning** = planning **actuel** du restaurant (slots publiés live), pas un snapshot de la ligne.
3. **Se connecter** = **un lien copiable**. L’admin le colle dans une **fenêtre de navigation privée** pour isoler la session. **Pas** d’ouverture auto d’onglet / fenêtre.

## Décisions figées

1. `generate_logs` gagne `restaurant_id` (nullable vieux rows) + `score_global` (nullable).
2. Voir = lecture seule, session admin **inchangée**. Pas d’édition, pas de generate, pas de sandbox.
3. Le lien impersonate est **à usage unique**, TTL **15 min**, consommé dans l’autre fenêtre. La session admin d’origine ne bouge pas.
4. Chrome table / gestes visibles = **file 73** (`admin-ui-pass.md` **gagne**) : encart note, hover warnings **sur la note**, Actions `impersonate` | `exporter vers le banc`. HTTP impersonate + GET planning **inchangés**.
5. Compte / resto disparu → 404, boutons inactifs.

## Persist (Alembic)

`generate_logs` :

- `restaurant_id` `String` nullable. **Pas** de FK (un resto peut disparaître, le log reste).
- `score_global` `Float` nullable.

Backfill : `restaurant_id` = `restaurateur_accounts.restaurant_id` où `email` (minuscules) = `generate_logs.email`. Pas d’account → laisser null. `score_global` des vieux rows → **null**.

Table `impersonate_tokens` :

```
token_hash  PK  (sha256 du opaque, comme sessions)
account_id  restaurateur visé
restaurant_id
expires_at
consumed_at  nullable
created_at
```

Jeton **opaque** `token_urlsafe`, hashé, jamais persisté en clair.

## Log generate

`_log_generate` écrit aussi :

- `restaurant_id` (déjà connu à l’appel)
- `score_global` = `slot.score.global` du cycle **venant d’être** généré (`null` si absent)

Publish manuel **n’écrit toujours pas** de log (`manual-planning.md`).

## `GET /v1/admin/generates`

Chaque entrée **ajoute** (clés toujours présentes) :

```
restaurant_id: string | null
score_global: float | null
```

Reste inchangé (`id`, `created_at`, `email`, `restaurant_name`, `team`, `search_effort`, `duration_seconds`, `engine_ref`, `facts`). Newest-first. 403 / 401 / 503 inchangés.

## Voir le planning (actuel)

```
GET /v1/admin/restaurants/{restaurant_id}/cycles     Bearer admin → 200 Cycles
GET /v1/admin/restaurants/{restaurant_id}/context    Bearer admin → 200 Context
```

Même JSON que `GET /v1/cycles` et `GET /v1/context` **de ce resto** (pas un snapshot du generate).  
`invite_token` des fiches : **inclus** (même forme que le GET restaurateur).

Inconnu / company absente → 404 `Restaurant introuvable.`  
Non-admin 403 `Action réservée à l’admin.` Sans session 401. Sans DB 503.

**Pas** de PATCH / generate / live sandbox admin. Lecture seule.

SPA : `/admin/planning/{restaurant_id}` → `index.html` (ajouter la route FastAPI comme `/admin/bench/run/{run_id}`).

## Se connecter (lien copiable)

```
POST /v1/admin/impersonate     Bearer admin
  body { "restaurant_id": "<id>" }
  200  { "url": "https://<host>/impersonate/<token>", "expires_at": ISO UTC }

POST /v1/auth/impersonate      public (pas de Bearer)
  body { "token": "<opaque>" }
  200  { "token": "<session>", "me": { kind: "company", email, restaurant_id, employee_id: null, admin: false } }
```

`url` **absolue**. Host = `X-Forwarded-Proto` + `X-Forwarded-Host` s’ils existent, sinon `request.base_url`. Path **`/impersonate/{token}`** (jeton **en clair dans l’URL**, une fois).

Mint :

- `restaurant_id` manquant / type faux → 400 `Champs invalides.`
- Company ou compte restaurateur absent → 404 `Restaurant introuvable.`
- TTL **15 minutes**. Un jeton par POST (plusieurs liens OK, chacun one-shot).

Consume :

- Inconnu / expiré / déjà `consumed_at` → 401 `Lien expiré ou déjà utilisé.`
- Succès : `consumed_at = now`, **nouvelle** session company **comme un login** (`SESSION_TTL` 30 j, hash opaque). `me.admin` = `is_admin` **du compte visé** (presque toujours `false`).
- **Ne** touche **pas** aux autres sessions (admin dans l’autre fenêtre reste admin).

SPA : `/impersonate/{token}` → `index.html`. Page **sans** session : POST consume, `sessionStorage` du token, `go("/planning")`. Échec → message `detail`, **pas** de login silencieux.

## UI — `/admin`

File 70 a ajouté `score_global` / `restaurant_id` au parser et les routes planning / impersonate.

**Chrome table (colonnes, hover, boutons)** = `admin-ui-pass.md` (**gagne**, file 73). Ne plus suivre le tableau Warnings / Planning / clic droit de ce file.

`/admin/planning/{id}` : `me.admin` seulement (sinon message réservé, 0 fetch). Titre = nom du resto. Menu admin (Historique | Banc | Stats). **Reprend** la grille `/planning` en **lecture seule** : 4 crans, recaps, export client si déjà branché sur les cycles chargés. **Pas** (Re)Calculer, **pas** « Entrer en mode édition », **pas** overlay live. Load = les deux GET admin. 404 → `Restaurant introuvable.`

`/impersonate/{token}` : pas d’exigence `me.admin`. Visible anonyme.

Parser `AdminGenerateEntry` : `restaurant_id` et `score_global` (number fini ou `null`).

## Tests

Infra (`skipif` sans `DATABASE_URL`) :

- Generate 200 → log a `restaurant_id` + `score_global` = globale du slot.
- GET generates : les deux clés présentes ; vieux row simulé null/null.
- GET cycles/context admin = même published / name que le GET company de ce resto.
- Resto inconnu → 404. Non-admin → 403.
- POST impersonate → `url` contient `/impersonate/` ; consume 200 `kind: company` du resto ; 2ᵉ consume 401 ; expiré 401.
- Session admin d’origine encore valide après consume (autre token).
- SPA routes `/impersonate/{token}` et `/admin/planning/{id}` servent `index.html` si `dist` présent (skip sinon).

UI file 70 : parser + routes planning / impersonate. Chrome table file 73.

## Hors freeze

Import resto → banc (file 71). Ranger le chrome banc (file 72). Repasse chrome table (file 73). Jeux cuisine. Un moteur par resto.
