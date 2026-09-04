## Why

Le moteur et le contrat d’exemple existent (`GET /v1/examples/saint-cloud`), mais le restaurateur n’a encore aucune application pour *voir* le cycle. Un rapport HTML et un canvas IDE ne sont pas le produit. Il faut un client React qui affiche le snapshot tel que le moteur l’a déjà scoré.

## What Changes

- Ajouter une SPA React + TypeScript (Vite) : premier écran utile = grille papier 14 jours (semaines A / B) + liste des warnings, à partir du JSON exemple.
- Afficher aussi les compteurs `planning.stats`, le tableau légal (`legal` + `legal_rows`) et le tableau souhaits (`wish_cols` + `wish_rows`) — forme de [la démo](https://1mbc.github.io/doux-planning/) et du canvas `exemple-restau-planning`, pas une copie du moteur.
- Consommer `GET /v1/examples/saint-cloud` pour la grille. Aucune génération, aucun score, aucune décision dans le front.
- Écrans **connexion** et **inscription** (`/register`) selon `contracts/http/v1-auth.md` : un login (email + mot de passe, `kind` depuis `me`) ; register Entreprise / Salarié (pas « restaurateur ») ; QR = même register + query `company_code` + `employee_token`. Pas de « mot de passe oublié ». Password ≥ 8. Afficher `detail` API tel quel.
- Token en `sessionStorage`, header `Authorization: Bearer` uniquement sur register/login/logout/`GET /v1/me`. **Pas** sur `/v1/examples/*` ni `/v1/sandbox/*`. Sans session : auth **et** exemple Saint-Cloud restent accessibles (« Voir l’exemple »). Ne pas bloquer la grille derrière le login.
- `kind: employee` : pas de Mode édition ; phrase FR (planning publié personnel plus tard). `kind: company` : grille + sandbox comme aujourd’hui.
- UX en français. Les messages moteur anglais sont présentés, pas recalculés.
- Ne pas archiver ni synchroniser. Ne pas modifier `src/doux_planning/`, `contracts/`, Compose, Alembic.

## Capabilities

### New Capabilities

- `planning-ui`: application web du snapshot d’exemple (grille 14 jours, warnings, stats, grilles légal / souhaits) plus écrans login / register / session.

### Modified Capabilities

- (aucune — le moteur et ses exigences restent dans `define-planning-core`)

## Impact

Uniquement `web/`. Proxy Vite `/v1` inchangé. L’API auth tourne à part (ne pas merger `auth/infra` / `auth/core`). Types = JSON du contrat ; clé manquante → throw. Pas de nouvelle dépendance (pas de react-router). Version `0.7.0`. Hors slice : rotate invite-token, panneaux contexte, wizard équipes, grille employé colorée, generate.
