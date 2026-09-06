# Export planning (client)

Freeze **UI**. **Pas** de nouvelle route HTTP. Tout se fait dans le navigateur à partir du cycle **déjà** chargé (`GET /v1/cycles` + context).  
Équipe **courante** seulement. Company `/planning`. Pas salarié, pas `/exemple`, pas `/context`.

Un menu **Exporter** (sous Calculer / Mode édition, ou dans `planning-actions`). Actif ssi `published[team]` non null. En **Mode édition** : désactivé (on exporte le cycle publié, pas le brouillon).

Quatre formats, même source (chiffres = payload, **pas** recalculés. Warnings `message` tel quel) :

| Format | Contenu |
|---|---|
| **JSON** | `{ export_version: 1, kind: "planning", team, restaurant_name, week_labels, employees` (fiches équipe, **sans** `invite_token`), `assignments, warnings, stats, legal_cols, legal_rows, wish_cols, wish_rows }` |
| **CSV** | métadonnées (nom, équipe, libellés) + grille plate : personne, jour, service, début, fin, heures |
| **XLSX** | **pas** le dump CSV. Canvas resto : **2 feuilles** Semaine A / B (ou Paire / Impaire). Titre **Planning validé en date du :** + horodatage local d’export. Colonnes Lun–Dim, chaque jour **DEBUT / FIN / NB HEURES**. **Une ligne par personne × service offert** (PDJ / DJ / Dîner — ids `morning` / `midday` / `evening` présents dans `context.services`). Case vide = repos / pas de shift. Couleurs d’en-tête + bandes (lisible). Lib `xlsx` / SheetJS |
| **JPEG** | image des **deux** feuilles semaine (A/B) telles qu’à l’écran. **2×** CSS pixels (`devicePixelRatio` ≥ 2), police lisible, `quality` ≥ 0.95. Lib OK |

Fichier : `{name-slug}-{salle\|cuisine}.{json\|csv\|xlsx\|jpg}` (`name` vide → `planning`).

## Hors freeze

Generate jobs / 3 boutons = `generate-jobs.md`. Admin / coerce (déjà landed). Archive / sync.
