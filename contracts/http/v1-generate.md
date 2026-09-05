# Generate live par équipe

Freeze HTTP. Wrappe `generate_team` (`contracts/domain/team-generate.md`).  
Bearer **company**. Pas d’id resto dans le path.  
`kind: employee` → 403 `Action réservée au restaurateur.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Exemple public + sandbox joujou **inchangés**. Pas de jobs / worker / `SKIP LOCKED` dans cette tranche. Sync : `POST` appelle `generate_team` et rend le cycle persisté. Tests = **`minimal`** seulement.

Tranche 16 : chaque cycle publié porte aussi le `CycleRecap` Core (`contracts/domain/cycle-recaps.md`) — **persist HTTP = brief Infra**. Assignments + warnings inchangés. Warning `rest_between_days` : `message` enrichi (deux horloges) déjà dans `EngineResult`.

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

`Shift` / `Warning` = mêmes clés que l’exemple / sandbox.  
Recap = wrap **`cycle_recap`** (`stats`, `legal_cols`, `legal_rows`, `wish_cols`, `wish_rows`) — **pas** de chiffres inventés dans `api/`.  
Assignments du cycle salle = `team: "salle"` seulement. L’autre clé reste le cycle déjà persisté (ou `null`), **avec** son recap s’il en a un.  
Cycle `null` : pas de clés recap. Cycle non null : les 5 clés recap **requises**.

### `GET /v1/cycles`

Même objet `published` (sans `team` / `search_effort` du dernier POST). Resto jamais généré : `{ "published": { "salle": null, "cuisine": null } }`.

## Persist

JSONB `published_cycles` : assignments + warnings + recap. Pas d’Alembic. Pas `example_snapshots` / `saint-cloud.json`.  
`reset_engine` / restart → même GET. Regenerer une équipe remplace seulement cette clé.  
Cycle déjà persisté **sans** recap : au GET, hydrater + `cycle_recap` (pas de 500).  
`POST /v1/live/sandbox/{team}/publish` → même `published` (recap inclus). Joujou + exemple 92 inchangés.

## UI (cette tranche)

Route `/planning` (company). **Calculer** si `ready[team]` ; POST `search_effort: "minimal"`. Grille = `published[team]` + fiches context. Pas d’édition sandbox live. Exemple sans session inchangé.

## Hors tranche

Worker, jobs, pastilles UI, `/me/shifts`, CORS sauf proxy cassé.
