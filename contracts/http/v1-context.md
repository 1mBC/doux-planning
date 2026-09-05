# Contexte restaurant live (GET / PATCH)

Freeze HTTP pour persister le domaine `contracts/domain/restaurant-context.md`.  
Bearer **company** uniquement. Pas d’id resto dans le path (session).  
`kind: employee` → 403 `Action réservée au restaurateur.`  
Sans / mauvais Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Exemple public + sandbox **inchangés** (public, dual-read). Pas de generate, pas de publish, pas de `/me/shifts`.

Infra wrappe Core (`empty_restaurant`, `team_ready`, `expand_typical_week`, types / semaine type, mutateurs). Ne pas réinventer `team_ready`. Si un symbole Core manque après merge `context/core` → stop, remonter au facteur.

Register `kind: company` crée déjà une `companies` vide. `GET /v1/context` doit renvoyer la forme vide (name `""`, services `[]`, ready faux) sans appeler `generate_cycle`.  
`legal_context_id` toujours `"france"` — id seulement, pas de copie des règles. Lecture seule (PATCH name OK, pas le légal).

## Routes

```
GET   /v1/context   Bearer company → 200 Context
PATCH /v1/context   Bearer company → 200 Context
POST  /v1/context/seed-example   Bearer company → 200 Context
```

`POST /v1/context/seed-example` : pas de body. Wrappe Core `seed_example_context`. Écrase le contexte persisté (fiches liées **incluses**). Vide `published_cycles` / `live_sandboxes` / `linked_employee_ids`. 200 = même `Context` que GET. **Hors slice Core** (Infra).

`PATCH` : clés **optionnelles**. Chaque clé fournie **remplace** cette section. Clés absentes inchangées. Corps vide = no-op 200.  
`week_labels` n’est pas une clé PATCH (dérivé).

## Body 200 — `Context`

```
{
  "name": "",
  "legal_context_id": "france",
  "company_code": "<invite_code>",
  "services": [],
  "ladders": { "salle": null, "cuisine": null },
  "employees": [],
  "types": [],
  "typical_week": { "salle": null, "cuisine": null },
  "ready": { "salle": false, "cuisine": false },
  "week_labels": "ab"
}
```

`ready.*` = `team_ready` Core, jamais un bool inventé côté HTTP.  
`week_labels` = `week_label_scheme` Core (`"ab"` | `"parity"`) — lecture seule, tout le resto. Ignoré en PATCH.

### `ladders.<team>`

`null` ou `{ "roles": [{ "name", "level" }], "substitution_explained": true }`.  
`level` entier ≥ 1. `substitution_explained` doit être `true` (règle déjà au domaine).

### `employees[]`

```
{
  "id", "name", "team": "salle"|"cuisine",
  "role": { "name", "level", "team" },
  "contractual_hours_per_week",
  "min_shift_hours",          // défaut 4 si omis à la création
  "unavailabilities": [{ "weekday", "service_id" }],
  "wellbeing": {
    "consecutive_rest": false,
    "weekend_rest_day": false,
    "weekend": null,
    "max_services": {},
    "max_coupures_per_week": null
  },
  "invite_token"
}
```

`invite_token` : généré par Core à la création de fiche, renvoyé au patron (QR). Ne pas l’accepter en PATCH pour **changer** un token (rotate = `POST /v1/staff/{id}/invite-token`).  
PATCH `employees` = liste **complète** (remplace). Les ids nouveaux : Core crée le token. Ids existants : garder le token déjà persisté.  
Une fiche déjà liée (`linked_employee_ids`) ne peut pas changer d’`id` ; la retirer de la liste alors qu’elle est liée → 409 `Cette fiche a déjà un compte.`

Après PATCH fiches : `GET /v1/invites/{company_code}` liste les **non liées** (name, role string, team) comme le freeze auth.

### `types[]`

```
{ "id", "name", "team", "service_id": "morning"|"midday"|"evening",
  "arrivals": [{ "time_minutes", "post_levels": [int] }],
  "departures": [{ "time_minutes", "remaining_post_levels": [int] }] }
```

Grille 15 min. PATCH `types` = liste complète.

### `typical_week.<team>`

`null` ou liste de cellules `{ "weekday", "service_id", "type_id": str|null, "closed": bool }`.  
`weekday` : `monday`…`sunday`. Cellule ouverte → `closed: false` + `type_id` d’un type du bon (team, service). Cellule fermée → `closed: true`, `type_id` null.  
PATCH `typical_week` remplace l’objet `{ salle, cuisine }` si la clé est envoyée.

`services` : liste 0..n parmi `morning`|`midday`|`evening`, sans doublon. Vide = resto pas encore configuré.

## PATCH body

Même clés que `Context`, toutes optionnelles, **sauf** `legal_context_id`, `company_code`, `ready`, `week_labels`, `invite_token` (sur une fiche) : ignorées ou 400 si on tente de les forcer.

`name` : string (peut rester `""`).

## Erreurs

`{ "detail": "<français>" }` comme auth.

| Cas | HTTP | `detail` |
|---|---|---|
| JSON / enum / grille 15 min / substitution false | 400 | `Champs invalides.` |
| Session | 401 | `Session invalide.` |
| Employé | 403 | `Action réservée au restaurateur.` |
| Retrait fiche liée | 409 | `Cette fiche a déjà un compte.` |
| Pas de Postgres | 503 | `Base indisponible.` |

## Persist

Étendre `companies` / `staff_fiches` (migration) : `legal_context_id`, services, échelles, types, semaine type, champs contrat / unavail / wellbeing / min_shift / role level.  
Ne pas écrire `example_snapshots` ni `data/examples/saint-cloud.json`. Ne pas réutiliser la ligne `restaurants` Saint-Cloud.  
Restart process → même `GET /v1/context`. Auth + invites restent justes.

`staff_fiches.wellbeing` JSONB **objet** : inclut `weekend_rest_day` (bool). Clé absente au parse → `false`. Pas de nouvelle colonne / Alembic. `at_least_one_weekend_rest_day` → 400 `Champs invalides.`

## UI (wizard)

Route `/context` (session company). Ordre : rôles → fiches → services entreprise → types → semaine type. Salle / cuisine indépendantes. `ready` affiché, pas de generate. PATCH listes = remplacement complet (renvoyer l’autre équipe). Exemple sans session inchangé.

## Hors tranche

Generate, jobs, publish, lock sandbox, `GET /v1/me/shifts`, bouton UI seed, CORS sauf proxy cassé. `POST /v1/context/seed-example` = Infra après Core `seed_example_context`.
