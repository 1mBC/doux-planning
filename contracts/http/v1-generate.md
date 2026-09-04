# Generate live par équipe

Freeze HTTP. Wrappe `generate_team` (`contracts/domain/team-generate.md`).  
Bearer **company**. Pas d’id resto dans le path.  
`kind: employee` → 403 `Action réservée au restaurateur.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Exemple public + sandbox joujou **inchangés**. Pas de jobs / worker / `SKIP LOCKED` dans cette tranche. Sync : `POST` appelle `generate_team` et rend le cycle persisté. Tests = **`minimal`** seulement.

Pas de `legal_rows` / `wish_rows` / `stats` moteur recréés côté HTTP. Assignments + warnings du `EngineResult` seulement.

## Routes

```
POST /v1/generate     Bearer company → 200 GenerateResult
GET  /v1/cycles       Bearer company → 200 Cycles
```

### `POST /v1/generate`

```
{ "team": "salle"|"cuisine", "search_effort": "minimal"|"optimized"|"maximal" }
```

`search_effort` omis → `optimized`.  
`TeamNotReady` → 409 `Cette équipe n'est pas prête à calculer.` (aucun solve).  
Team / effort invalide → 400 `Champs invalides.`

200 = `GenerateResult` :

```
{
  "team": "salle",
  "search_effort": "minimal",
  "published": {
    "salle": { "assignments": [Shift], "warnings": [Warning] },
    "cuisine": null
  }
}
```

`Shift` / `Warning` = mêmes clés que l’exemple / sandbox (`employee_id`, `day_index`, `weekday`, `service_id`, `team`, `start_minutes`, `end_minutes`, `post_level`, `duration_hours` ; `severity`, `code`, `message`, `employee_id`, `day_index`).  
Assignments du cycle salle = `team: "salle"` seulement. L’autre clé reste le cycle déjà persisté (ou `null`).

### `GET /v1/cycles`

Même objet `published` (sans `team` / `search_effort` du dernier POST). Resto jamais généré : `{ "published": { "salle": null, "cuisine": null } }`.

## Persist

JSONB (ou tables) sur l’entreprise live — **pas** `example_snapshots`, pas `data/examples/saint-cloud.json`.  
`reset_engine` / restart → même `GET /v1/cycles`. Regenerer une équipe remplace seulement cette clé.

## Hors tranche

Worker, jobs, sandbox live, publish semaine, `/me/shifts`, UI Calculer, CORS sauf proxy cassé.
