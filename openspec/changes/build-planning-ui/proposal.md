## Why

Le moteur et le contrat d’exemple existent (`GET /v1/examples/saint-cloud`), mais le restaurateur n’a encore aucune application pour *voir* le cycle. Un rapport HTML et un canvas IDE ne sont pas le produit. Il faut un client React qui affiche le snapshot tel que le moteur l’a déjà scoré.

## What Changes

- Ajouter une SPA React + TypeScript (Vite) : premier écran utile = grille papier 14 jours (semaines A / B) + liste des warnings, à partir du JSON exemple.
- Afficher aussi les compteurs `planning.stats`, le tableau légal (`legal` + `legal_rows`) et le tableau souhaits (`wish_cols` + `wish_rows`) — forme de [la démo](https://1mbc.github.io/doux-planning/) et du canvas `exemple-restau-planning`, pas une copie du moteur.
- Consommer `GET /v1/examples/saint-cloud` pour la grille. Aucune génération, aucun score, aucune décision dans le front.
- Écrans **connexion** et **inscription** (`/register`) selon `contracts/http/v1-auth.md` : un login (email + mot de passe, `kind` depuis `me`) ; register Entreprise / Salarié (pas « restaurateur ») ; QR = même register + query `company_code` + `employee_token`. Pas de « mot de passe oublié ». Password ≥ 8. Afficher `detail` API tel quel.
- Token en `sessionStorage`, header `Authorization: Bearer` uniquement sur register/login/logout/`GET /v1/me`. **Pas** sur `/v1/examples/*` ni `/v1/sandbox/*`. Sans session : auth **et** exemple Saint-Cloud restent accessibles (« Voir l’exemple »). Ne pas bloquer la grille derrière le login.
- `kind: employee` : pas de Mode édition, pas de wizard `/context` (403 API). Route `/planning` (lien chrome « Planning ») selon `contracts/http/v1-me-planning.md` : `GET /v1/me/planning` Bearer, grille équipe, highlight de ses lignes, panneau contrat / indispos / souhaits lecture seule. Pas de Calculer ni live sandbox.
- `kind: company` : route `/context` (lien « Mon restaurant ») — wizard selon `contracts/domain/wizard-ui.md` : **Services → Rôles → Équipe → Souhaits → Services types → Semaine type**. Services types : cartes chrono (pas de tableur), horloge + ±15, STAFF = sac seul, pire-cas → `remaining_post_levels`. Rôles : Nom + Niveau stepper. Invite : URL **absolue** + QR. `weekend_rest_day` en **colonne** à part. Bearer sur GET/PATCH `/v1/context` et `POST /v1/context/seed-example`.
- `kind: company` : bouton **Intégrer l’exemple Saint-Cloud** sur `/context` (bandeau, à côté du code). Tous les comptes restaurateur. Confirm FR puis `POST /v1/context/seed-example` (Bearer, pas de body). 200 = même `Context` que GET. Pas de generate, pas d’aller sur `/planning`. Pas de bouton salarié / exemple / planning / login.
- `kind: company` : route `/planning` selon `contracts/http/v1-generate.md` + `cycle-recaps.md` : **Calculer** si `ready[team]`, POST `minimal`. Cycle non null : parser `stats` / `legal_cols` / `legal_rows` / `wish_cols` / `wish_rows` (clé manquante → throw). Hors édition : pastilles + tableaux légal / **Souhaits bien-être**. Warning `contract_hours` → pastille **Contrat** ; cellule `ok: false` orange + gras. **Calculer** / **Mode édition** sous Salle · Cuisine. Mode édition : cacher les recaps. Warnings `message` tel quel.
- `/exemple` lit le snapshot **rafraîchi** (`exemple-snapshot.md`) : 92 / 0 / 0 / 47 / 84 % / 10 / 12, **17** warnings FR, `wish_cols` live (pas `we1j` / `weA`). Chrome v0.16.0 inchangé.
- `kind: company` : **Mode édition** sur `/planning` si `published[team]` existe — `POST /v1/live/sandbox/{team}/enter` (Bearer) selon `contracts/http/v1-live-sandbox.md`. Même overlays que le joujou (retune ±15 Valider, replace, swap, fill). Lecture sans discard. Publier → `POST .../publish` puis grille = `GET /v1/cycles`. Zéro appel `/v1/sandbox/*` depuis `/planning`. `/exemple` joujou inchangé (public).
- UX en français. Les messages moteur anglais sont présentés, pas recalculés.
- Ne pas archiver ni synchroniser. Ne pas modifier `src/doux_planning/`, `contracts/`, Compose, Alembic.

## Capabilities

### New Capabilities

- `planning-ui`: application web du snapshot d’exemple, login / register / session, wizard contexte, cycle publié (Calculer), édition live du cycle, et grille salarié.

### Modified Capabilities

- (aucune — le moteur et ses exigences restent dans `define-planning-core`)

## Impact

Uniquement `web/`. Proxy Vite `/v1` inchangé. API = uvicorn sur `master`. Version `0.18.0`. Hors slice : exports, admin, rotate invite-token.
