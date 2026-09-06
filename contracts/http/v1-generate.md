# Generate live par équipe

Freeze HTTP. Wrappe `generate_team` (`contracts/domain/team-generate.md`).  
Jobs Maximal = `contracts/domain/generate-jobs.md`.  
**3 versions** + `generated_at` = `contracts/domain/generate-versions.md` (gagne sur la forme `published`).  
Bearer **company**. Pas d’id resto dans le path.  
`kind: employee` → 403 `Action réservée au restaurateur.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Exemple public + sandbox joujou **inchangés**. **Pas** de Core `engine.py`.  
`minimal` / `optimized` : 200 sync. `maximal` : 202 + worker. Tests sync = `minimal` ; job = tick stub.

## Routes

```
POST /v1/generate                  Bearer company → 200 GenerateResult | 202 GenerateJob
GET  /v1/generate/jobs/{job_id}    Bearer company → 200 GenerateJob
GET  /v1/cycles                    Bearer company → 200 Cycles
```

### `POST /v1/generate`

```
{ "team": "salle"|"cuisine", "search_effort": "minimal"|"optimized"|"maximal" }
```

Omis → `optimized` (200). `TeamNotReady` → 409. Effort / team invalide → 400.  
`maximal` déjà queued/running cette team → 409 `Un calcul maximal est déjà en cours.`

200 :

```
{
  "team": "salle",
  "search_effort": "minimal",
  "published": {
    "salle": {
      "versions": {
        "minimal": { assignments, warnings, stats, legal_*, wish_*, generated_at, search_effort, duration_seconds },
        "optimized": null,
        "maximal": null
      },
      "latest": "minimal"
    },
    "cuisine": null
  }
}
```

Équipe sans aucun calcul : `null` (pas d’objet versions vide obligatoire — ou objet tout-null + `latest` null ; **un** des deux, Infra choisit et GET/POST **identiques**). Préférer l’objet `{ versions: {3× null}, latest: null }` dès le premier generate de l’autre équipe.

`maximal` → 202 `{ job_id, team, search_effort, status: queued, estimated_seconds: 600 }` (pas de `published`).

### `GET /v1/generate/jobs/{job_id}`

Comme aujourd’hui. `published` ssi `done` = **nouveau** format versions.

### `GET /v1/cycles`

Même `published` (deux équipes, versions). Jamais généré : `{ "published": { "salle": null, "cuisine": null } }`.

## Persist

JSONB `published_cycles` : 3 slots + `latest`. Coerce ancien plat → `versions.optimized`.  
Generate écrit **un** slot + `generated_at` + `search_effort` + `duration_seconds` + `latest`.  
Worker logs stdout : `generate-versions.md`. `generate_logs` : `admin.md`.

## UI

Sélecteur d’effort **sans** solve ; (Re)Calculer POST. Détail = brief UI.

## Hors tranche

`/me/shifts`, mail / push, Core limites de recherche.
