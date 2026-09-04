## Why

Le moteur et le contrat d’exemple existent (`GET /v1/examples/saint-cloud`), mais le restaurateur n’a encore aucune application pour *voir* le cycle. Un rapport HTML et un canvas IDE ne sont pas le produit. Il faut un client React qui affiche le snapshot tel que le moteur l’a déjà scoré.

## What Changes

- Ajouter une SPA React + TypeScript (Vite) : premier écran utile = grille papier 14 jours (semaines A / B) + liste des warnings, à partir du JSON exemple.
- Afficher aussi les compteurs `planning.stats`, le tableau légal (`legal` + `legal_rows`) et le tableau souhaits (`wish_cols` + `wish_rows`) — forme de [la démo](https://1mbc.github.io/doux-planning/) et du canvas `exemple-restau-planning`, pas une copie du moteur.
- Consommer **uniquement** `GET /v1/examples/saint-cloud`. Aucune autre route. Aucune génération, aucun score, aucune décision dans le front.
- UX restaurateur en français. Les messages moteur anglais sont présentés, pas recalculés.
- Ne pas archiver ni synchroniser `define-planning-core`. Ne pas modifier `src/doux_planning/` hors `api/` (CORS éventuel uniquement).

## Capabilities

### New Capabilities

- `planning-ui`: application web lecture seule du snapshot d’exemple (grille 14 jours, warnings, stats, grilles légal / souhaits).

### Modified Capabilities

- (aucune — le moteur et ses exigences restent dans `define-planning-core`)

## Impact

Nouveau dossier `web/` (Vite + React + TypeScript). Processus de dev : `uvicorn` + `vite` (proxy `/v1` vers l’API). Possible middleware CORS dans `src/doux_planning/api/app.py` ; pas de nouvelle route. Moteur, JSON exemple, et change `define-planning-core` inchangés.
