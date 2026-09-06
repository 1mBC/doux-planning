# Generate live par équipe

Freeze HTTP. Wrappe `generate_team` (`contracts/domain/team-generate.md`).  
Jobs Maximal = `contracts/domain/generate-jobs.md` (gagne sur le 202 / poll).  
Bearer **company**. Pas d’id resto dans le path.  
`kind: employee` → 403 `Action réservée au restaurateur.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Exemple public + sandbox joujou **inchangés**.  
`minimal` / `optimized` : sync dans la requête. `maximal` : **202** + worker + `GET /v1/generate/jobs/{id}`. Tests sync = **`minimal`** ; tests job = tick stub (pas 600 s).

Tranche 16 : chaque cycle publié porte aussi le `CycleRecap` Core (`contracts/domain/cycle-recaps.md`). Assignments + warnings inchangés.

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

`search_effort` omis → `optimized` (**200** sync).  
`TeamNotReady` → 409 `Cette équipe n'est pas prête à calculer.` (aucun solve, aucun job).  
Team / effort invalide → 400 `Champs invalides.`  
`maximal` déjà `queued`/`running` pour cette company+team → 409 `Un calcul maximal est déjà en cours.`

`minimal` / `optimized` → **200** `GenerateResult` :

```
{
  "team": "salle",
  "search_effort": "minimal",
  "published": {
    "salle": {
      "assignments": [Shift],
      "warnings": [Warning],
      "stats": { ... },
      "legal_cols": [...],
      "legal_rows": [...],
      "wish_cols": [...],
      "wish_rows": [...]
    },
    "cuisine": null
  }
}
```

`maximal` → **202** `GenerateJob` (pas de `published`) :

```
{ "job_id", "team", "search_effort": "maximal", "status": "queued", "estimated_seconds": 600 }
```

`Shift` / `Warning` = mêmes clés que l’exemple / sandbox.  
Recap = wrap **`cycle_recap`**. Assignments du cycle salle = `team: "salle"` seulement.

### `GET /v1/generate/jobs/{job_id}`

Même resto. 200 :

```
{ "job_id", "team", "search_effort", "status", "estimated_seconds",
  "error"?: string,
  "published"?: <même published que GenerateResult> }
```

`status` : `queued` | `running` | `done` | `failed`.  
`published` ssi `done`. `error` ssi `failed`.  
Autre company / id inconnu → 404. Employee → 403.

### `GET /v1/cycles`

Même objet `published` (sans `team` / `search_effort` du dernier POST). Resto jamais généré : `{ "published": { "salle": null, "cuisine": null } }`.

## Persist

JSONB `published_cycles` : assignments + warnings + recap.  
Table `generate_jobs` (Alembic). Worker SKIP LOCKED. Succès job = même persist + `generate_logs` qu’un 200.  
`reset_engine` / restart → même GET cycles. Regenerer une équipe remplace seulement cette clé.  
Cycle déjà persisté **sans** recap : au GET, hydrater + `cycle_recap` (pas de 500).  
`POST /v1/live/sandbox/{team}/publish` → même `published` (recap inclus). Joujou + exemple 92 inchangés.

## UI

Route `/planning` (company). **Trois** boutons si `ready[team]` : Minimal · Optimisé · Maximal.  
Loader ≥ 1 s. Maximal = POST 202 puis poll GET job. Détail = brief UI.

## Hors tranche

`/me/shifts`, CORS sauf proxy cassé, mail / push.
