## Why

Le moteur et le contrat d’exemple existent (`GET /v1/examples/saint-cloud`), mais le restaurateur n’a encore aucune application pour *voir* le cycle. Un rapport HTML et un canvas IDE ne sont pas le produit. Il faut un client React qui affiche le snapshot tel que le moteur l’a déjà scoré.

## What Changes

- Ajouter une SPA React + TypeScript (Vite) : premier écran utile = grille papier 14 jours (semaines A / B) + liste des warnings, à partir du JSON exemple.
- Afficher aussi les compteurs `planning.stats`, le tableau légal (`legal` + `legal_rows`) et le tableau souhaits (`wish_cols` + `wish_rows`) — forme de [la démo](https://1mbc.github.io/doux-planning/) et du canvas `exemple-restau-planning`, pas une copie du moteur.
- Consommer `GET /v1/examples/saint-cloud` pour la grille. Aucune génération, aucun score, aucune décision dans le front.
- Écrans **connexion** et **inscription** (`/register`) selon `contracts/http/v1-auth.md` : un login (email + mot de passe, `kind` depuis `me`) ; register Entreprise / Salarié (pas « restaurateur ») ; QR = même register + query `company_code` + `employee_token`. Pas de « mot de passe oublié ». Password ≥ 8. Afficher `detail` API tel quel.
- Token en `sessionStorage`, header `Authorization: Bearer` uniquement sur register/login/logout/`GET /v1/me`. **Pas** sur `/v1/examples/*` ni `/v1/sandbox/*`. Sans session : auth **et** exemple Saint-Cloud restent accessibles (« Voir l’exemple »). Ne pas bloquer la grille derrière le login.
- `kind: employee` : pas de Mode édition, pas de wizard `/context` (403 API). Route `/planning` (lien chrome « Planning ») selon `contracts/http/v1-me-planning.md` : `GET /v1/me/planning` Bearer, grille équipe, highlight de ses lignes, panneau contrat / indispos / souhaits lecture seule. Pas de Calculer ni live sandbox.
- `kind: company` : route `/context` (lien « Mon restaurant ») — wizard contexte selon `contracts/http/v1-context.md` : identité (nom PATCH, légal France lecture seule, `company_code`) puis rôles → fiches → services → types → semaine type. Salle et cuisine indépendantes. `ready.*` affiché tel quel (badges FR). Bearer sur GET/PATCH `/v1/context` en plus de l’auth. Toujours pas sur exemple / sandbox.
- `kind: company` : route `/planning` (lien « Planning ») selon `contracts/http/v1-generate.md` : GET `/v1/cycles` + GET `/v1/context`, sélecteur équipe, **Calculer** seulement si `ready[team]` (JSON context, pas un bool inventé), POST `{ team, search_effort: "minimal" }`. Grille 14 j. + warnings du cycle publié. Pas de stats / legal_rows / wish_rows inventés. Salarié : 403 / pas d’écran. Bearer sur `/v1/generate` et `/v1/cycles`.
- `kind: company` : **Mode édition** sur `/planning` si `published[team]` existe — `POST /v1/live/sandbox/{team}/enter` (Bearer) selon `contracts/http/v1-live-sandbox.md`. Même overlays que le joujou (retune ±15 Valider, replace, swap, fill). Lecture sans discard. Publier → `POST .../publish` puis grille = `GET /v1/cycles`. Zéro appel `/v1/sandbox/*` depuis `/planning`. `/exemple` joujou inchangé (public).
- UX en français. Les messages moteur anglais sont présentés, pas recalculés.
- Ne pas archiver ni synchroniser. Ne pas modifier `src/doux_planning/`, `contracts/`, Compose, Alembic.

## Capabilities

### New Capabilities

- `planning-ui`: application web du snapshot d’exemple, login / register / session, wizard contexte, cycle publié (Calculer), édition live du cycle, et grille salarié.

### Modified Capabilities

- (aucune — le moteur et ses exigences restent dans `define-planning-core`)

## Impact

Uniquement `web/`. Proxy Vite `/v1` inchangé. L’API salarié tourne à part (ne pas merger `employee/infra` / `employee/core`). Types = JSON du contrat ; clé manquante → throw. Pas de nouvelle dépendance. Version `0.11.0`. Hors slice : rotate invite-token, `optimized` 30 s, edit contraintes salarié.
