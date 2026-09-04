# Tranche 2 — édition sandbox HTTP

Python Core : `preview_retune(id, shift, start, end)` **un essai** ; replace/swap classés au **delta** ; chaque proposition a `impact` (dont `role_fit`) + `current_score` / `trial_score`.  
Infra wrappe, ne rescore pas. `GET /v1/examples/saint-cloud` inchangé.

Pas d’auth. Cible `cycle`. Sync. Pas de `generate_cycle`.

## Shift

Égalité moteur : `employee_id`, `day_index`, `weekday`, `service_id`, `team`, `start_minutes`, `end_minutes`, `post_level`.  
`duration_hours` en lecture. `partner` **doit** renvoyer `day_index` et `weekday` (l’UI affiche le jour avant l’heure).

## Score (`_attempt_key`, ordre keep-best)

```
{
  "empty": int,
  "interdit": int,
  "hours_miss": number,
  "souhait": int,
  "below_role": int,
  "overqualification": int
}
```

Plus petit = meilleur. L’UI affiche avant → après, elle ne recalcule pas.

## Impact (seul résumé autorisé pour l’overlay)

```
{
  "new_interdits": [ Warning… ],
  "broken_wishes": [ Warning… ],
  "contract": [
    {
      "employee_id": string,
      "week_start": 0 | 7,
      "current_hours": number,
      "trial_hours": number,
      "contracted": number,
      "kind": "closer" | "farther" | "excess"
    }
  ],
  "coverage_added": [ Warning… ],
  "coverage_removed": [ Warning… ],
  "role_fit": [
    {
      "current_gap": int,
      "trial_gap": int,
      "kind": "better" | "worse"
    }
  ]
}
```

`contract` = uniquement les personnes du geste.  
`role_fit` : 0 ou 1 entrée. `gap` = `employee.level - post_level` (même terme que `_overqualification`) **sur le créneau cliqué seulement** (retune / replace / swap = le `shift` du preview, pas le partenaire). `better` si trial < current, `worse` si trial > current. **Omettre** si égal ou occupant manquant (retune même poste, swap de mêmes niveaux sur ce poste, fill d’une case vide). Pas de `delta.unchanged`. Ne pas renvoyer la liste brute `warnings` du trial 14 j. Pas de phrase UX dans le JSON.

## Routes

Enter / GET / undo / persist : inchangés vs freeze précédent, **plus** `score` (score du draft courant) sur l’état sandbox.

`history[]` n’est plus seulement `{ index, gesture }`. Chaque cran :

```
{
  "index": 1,
  "gesture": "retune" | "replace" | "swap" | "fill",
  "shift": Shift | null,
  "slot": { employee_id, day_index, weekday, service_id, team } | null,
  "employee_id": string | null,
  "start_minutes": int | null,
  "end_minutes": int | null,
  "partner": Shift | null,
  "impact": { … }
}
```

`shift` = créneau occupé du commit ; `slot` = case vide du fill. Rempli au commit depuis le body + la proposition choisie (pas un second score). Undo pop le dernier. GET / enter / commit / undo / discard renvoient cette liste. Dual-read Postgres : persister ces recaps (plus seulement le nom du geste).

### `POST /v1/sandbox/preview`

**Replace / swap** (liste) :

```
{ "gesture": "replace" | "swap", "shift": { …Shift } }
```

200 `{ "proposals": [ Proposal, … ] }` tri `rank` croissant.

**Retune** (un essai) :

```
{
  "gesture": "retune",
  "shift": { …Shift courant },
  "start_minutes": int,
  "end_minutes": int
}
```

Appelle `preview_retune(..., start_minutes, end_minutes)`. 200 `{ "proposals": [ Proposal ] }` (0 ou 1).  
`IdentityRetuneError` → 400 français (horaires identiques). Durée < min → 400 français. Shift absent → 404.

**Fill** (case vide, liste) :

```
{
  "gesture": "fill",
  "slot": {
    "employee_id": string,
    "day_index": int,
    "weekday": string,
    "service_id": "midday" | "evening",
    "team": string
  },
  "start_minutes": int | null,
  "end_minutes": int | null
}
```

Appelle `preview_fill`. Heures omises / null → span structure (1re arrivée → dernière départ). `post_level` = `role.level` de la personne de la **ligne**.  
200 `{ "proposals": [ Proposal, … ] }` : **rang 1 = la personne de la ligne** si elle peut tenir le poste ; le reste classé `occupied_sort_key`. `gesture` `"fill"`.  
Déjà occupé (un assignment existe pour cette personne / jour / service) → 409 français (l’UI doit ouvrir l’overlay occupé). Service fermé / durée min → 400. Pas de sandbox → 404.

### `POST /v1/sandbox/commit`

Comme avant. Retune : `start_minutes` + `end_minutes` **obligatoires**.  
Fill : `slot` + `employee_id` + `start_minutes` + `end_minutes` ; Infra rappelle `preview_fill` et matche `employee_id`.

### `POST /v1/sandbox/discard`

`discard_sandbox` puis `enter_sandbox(..., "cycle")` (brouillon = cycle publié / hydraté, historique vide). 200 = même shape que enter. Pas de sandbox → 404 français. Ne réécrit pas l’example. Dual-read : supprimer la session persistée puis réécrire l’état neuf.

## Proposal

```
{
  "rank": 1,
  "gesture": "retune" | "replace" | "swap" | "fill",
  "start_minutes": int | null,
  "end_minutes": int | null,
  "employee_id": string | null,
  "partner": Shift | null,
  "impact": { … },
  "current_score": { …Score },
  "trial_score": { …Score }
}
```

Pas de `delta`, pas de `warnings` (hors `impact.*`). Pas d’`assignments`.

## État sandbox

Comme avant, plus `"score": { …Score }` du draft ouvert.

## Hors scope

Auth, jobs, publish, week, React, moteur hors `api/` (sauf appeler `discard_sandbox` / `enter_sandbox` déjà là). Pas d’invention d’heures dans l’UI : le span structure vient du preview fill.
