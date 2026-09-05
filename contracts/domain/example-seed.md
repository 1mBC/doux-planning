# Seed exemple → resto live

Freeze **domaine**. HTTP / bouton = briefs suivants.

Un clic restaurateur (pré-BETA, **tous** les comptes company) remplit le contexte depuis **Saint-Cloud fichier** (`data/examples/saint-cloud.json`).  
**Écrase** rôles, équipe, types, semaine type, services, heures, souhaits, indispos.  
**Ne copie pas** le planning / assignments / `published_cycles` / `live_sandboxes` / `cycle`.  
**Garde** `identity.id`, `identity.name` (pas « Saint-Cloud »), `legal_context_id`.

## API

```
seed_example_context(state) -> RestaurantState
```

Source = section `restaurant` du JSON (employees, hours, structures). **Pas** `planning.assignments`. Ne pas appeler `generate_cycle`. `hydrate_delivered_cycle` **interdit** ici (il pose un cycle + sandbox joujou).

### Mapping structures → contexte live

Saint-Cloud n’a pas `types` / `typical_week` / `ladders` : les dériver.

- `company_services` + `hours` = `restaurant.hours` (Saint-Cloud : `midday`, `evening`, dimanche fermé).
- Chaque `structure` → `ServiceType` : même `id`, `team`, `service_id`, vagues ; `name` = `id` si pas de nom.
- `TypicalWeek` : pour **chaque** équipe × chaque service entreprise × lun–dim :
  - une structure de ce (team, service) dont `weekdays` contient le jour → `closed: false`, `type_id` = id structure ;
  - sinon `closed: true`, `type_id` null.
- `ladders` : une échelle par équipe **présente** sur les fiches exemple ; rôles = uniques `(name, level, team)` ; `substitution_explained: true`. Cuisine absente de Saint-Cloud → pas d’échelle cuisine.
- `employees` : fiches exemple (ids `diane`, `theo`, …), wellbeing / indispos **forme actuelle**, `forced_off_days` conservés. **Nouveau** `invite_token` par fiche (≠ `id`).
- `structures` du state = `expand_typical_week` après coup (pas les structures brutes seules).
- `published_cycles` / `live_sandboxes` = `{ salle: None, cuisine: None }`. `cycle` = `None`. `accounts` = `[]`.

Après seed : `team_ready(salle)` **vrai**, `team_ready(cuisine)` **faux**. `week_label_scheme` selon les fiches (Saint-Cloud actuel → `"ab"`). Nom inchangé (`""` si encore vide).

## Tests

`empty_restaurant("co-1")` + seed → nom `""` ; ≥ 1 fiche salle ; services midday+evening ; types + semaine ; ready salle / pas cuisine ; published vides ; tokens ≠ id ; pas d’assignments.  
Seed une 2ᵉ fois (state déjà rempli + un cycle publié fictif) → published encore vides, fiches exemple.  
Pytest existants verts. Pas d’HTTP.

## Hors freeze

`POST /v1/context/seed-example`, smash JSONB / comptes salariés liés, bouton UI, archive.
