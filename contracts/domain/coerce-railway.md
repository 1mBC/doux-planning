# Coerce Railway (vieux JSON wellbeing à la lecture)

Freeze **Infra** (landed `coerce-railway/infra`). **Pas** d’Alembic. **Pas** de Core (`hydrate.py` / `staff.py` restent stricts).  
Railway a des `staff_fiches` écrites **avant** l’objet `Wellbeing`. Aujourd’hui `GET /v1/context` / generate / `/v1/me/planning` **400** sur ces lignes. On **lit** l’ancien JSONB → objet Core, puis on **réécrit** la ligne (heal).

PATCH / import **restent** 400 `Champs invalides.` sur une forme legacy (on n’accepte plus l’ancien côté client).

## Lecture (GET context, export, generate, me/planning, boot seed)

`wellbeing_from_json` + `unavailability_from_json` (codec `api/` seulement) :

| JSONB stocké | Objet émis / réécrit |
|---|---|
| `null` / `{}` / `[]` | `Wellbeing()` |
| liste de clés | mapping ci-dessous (clés inconnues **ignorées**) |
| objet avec clés retirées | mapping + garder les champs déjà nouveaux |
| objet déjà Core | inchangé (`weekend_rest_day` absent → `false`) |

### Liste / clés retirées → objet

| Ancienne clé (liste ou objet) | Après |
|---|---|
| `two_consecutive_rest_days` | `consecutive_rest: true` |
| `weekend_off_every_two_weeks` | `weekend: "every_two"` (si `weekend` déjà posé, **garder**) |
| `at_least_one_weekend_rest_day` | `weekend_rest_day: true` |
| `max_two_coupures_per_week` | `max_coupures_per_week: 2` |
| `max_three_coupures_per_week` | `max_coupures_per_week: 3` (si les deux → **2**, plus strict) |
| `no_evening_service` | `max_services.evening: 0` |
| `no_morning_service` | `max_services.morning: 0` |

`max_evenings_per_week` / `max_mornings_per_week` **sur la fiche** (pas dans `wellbeing`) : `N` → `max_services.evening` / `.morning` ; `null` / absent → clé absente. Puis **ne plus** les renvoyer.

### Indispos

Besoin des `services` entreprise (liste context).

| Stocké | Après |
|---|---|
| `{ weekday, service_id }` valide | inchangé |
| `every_morning: true` | `{ weekday, service_id: "morning" }` si `morning` offert, sinon drop |
| `every_evening: true` | idem `evening` |
| `service_id` null / absent (journée) | **une ligne par** service ouvert du resto |

Flags `every_*` ensuite **retirés**. Ligne sans weekday → drop.

## Heal (réécriture)

Après coerce, si le JSONB **diffère** de `wellbeing_to_json` / indispos nouvelles : `UPDATE` la fiche. GET suivant = déjà propre. Idempotent. Pas de job, pas d’Alembic.

GET / export / me/planning émettent **toujours** l’objet Core (jamais la liste).

## Écriture (inchangée)

`PATCH /v1/context` `employees[]` et `POST /v1/context/import` : liste de clés, clés retirées, `every_*`, `max_*_per_week` top-level → **400** `Champs invalides.`  
Exemple public / `saint-cloud.json` : **pas** de coerce (fichier déjà nouvel objet). **92 / 17 / 10/12**.

## Hors freeze

Archive / sync. File nuit close. Core hydrate.
