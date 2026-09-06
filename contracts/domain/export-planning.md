# Export planning (client)

Freeze **UI**. **Pas** de nouvelle route HTTP. Tout se fait dans le navigateur à partir du cycle **déjà** chargé (`GET /v1/cycles` + context).  
Équipe **courante** seulement. Company `/planning`. Pas salarié, pas `/exemple`, pas `/context`.

Un menu **Exporter** (sous Calculer / Mode édition, ou dans `planning-actions`). Actif ssi `published[team]` non null. En **Mode édition** : désactivé (on exporte le cycle publié, pas le brouillon).

Quatre formats, même source :

| Format | Contenu |
|---|---|
| **JSON** | payload d’affichage : `{ export_version: 1, kind: "planning", team, restaurant_name, week_labels, employees` (fiches équipe, **sans** `invite_token`), `assignments, warnings, stats, legal_cols, legal_rows, wish_cols, wish_rows }` |
| **CSV** | métadonnées (nom, équipe, libellés A/B) + grille : personne, jour, service, début, fin, heures |
| **XLSX** | même chose que CSV (feuille grille + métadonnées). Lib OK (`xlsx` / SheetJS) |
| **JPEG** | image des **deux** feuilles semaine (A/B) telles qu’à l’écran. Lib OK (`html2canvas` ou équivalent) |

Fichier : `{name-slug}-{salle\|cuisine}.{json\|csv\|xlsx\|jpg}` (`name` vide → `planning`).  
Chiffres = payload, **pas** recalculés. Warnings `message` tel quel.

## Hors freeze

Admin, coerce Railway, export config (déjà landed), archive / sync.