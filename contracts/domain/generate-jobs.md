# Generate jobs (hybride C)

Freeze **Infra**. UI boutons / loader / poll = brief UI ensuite.  
Pas de Core (`SEARCH_SECONDS` / `generate_team` inchangés). Pas d’email, pas de push.

## Hybride

| `search_effort` | HTTP | Solve |
|---|---|---|
| `minimal` (3 s) / `optimized` (30 s) | **200** sync, comme aujourd’hui | dans la requête |
| `maximal` (600 s) | **202** tout de suite | **worker** + poll |

Omis → `optimized` (sync). `TeamNotReady` → **409** `Cette équipe n'est pas prête à calculer.` **aucun** job.

## `POST /v1/generate` `maximal`

202 :

```
{ job_id, team, search_effort: "maximal", status: "queued", estimated_seconds: 600 }
```

**Pas** de `published` dans le 202. **Pas** d’appel `generate_team` dans le process web.

Un job `queued` ou `running` **pour cette company + team** → 409 `Un calcul maximal est déjà en cours.`  
L’autre équipe reste libre (sync ou maximal).

## `GET /v1/generate/jobs/{job_id}`

Bearer company, **même** resto. Autre company / id inconnu → 404. Employee → 403. Sans session 401. Sans DB 503.

```
{ job_id, team, search_effort, status, estimated_seconds,
  error?: string,
  published?: <même objet que GenerateResult.published> }
```

`status` : `queued` | `running` | `done` | `failed`.  
`published` **seulement** si `done` (recap inclus, comme un 200 sync).  
`error` **seulement** si `failed` (FR).  
`estimated_seconds` = 600 (borne moteur, pas un chrono live).

## Worker

Process **à part** (Compose `worker`, Railway 2ᵉ service, **même** image / `DATABASE_URL`).  
Boucle : `SELECT … FOR UPDATE SKIP LOCKED` un `queued` → `running` → `generate_team(…, maximal)` → persist `published_cycles` **comme** le 200 sync → `done`. Exception → `failed` + `error` FR.

Succès → **une** ligne `generate_logs` (même règle que POST 200). Échec / 409 : pas de log.

Pytest : **ne pas** attendre 600 s. Après POST 202, appeler **un tick** worker (fonction exportée) avec `generate_team` **stubbé** (cycle instantané). Pas de boucle sleep dans les tests.

## Deploy

`docker-compose.yml` : service `worker` (même build, commande worker, `depends_on` db).  
`Dockerfile` : garder uvicorn par défaut ; commande worker documentée (`python -m doux_planning.api.worker` ou équivalent).  
Railway : **2ᵉ service** même image, start = worker, **pas** de domaine public, mêmes `DATABASE_URL` / `ADMIN_EMAIL`. Alembic **OK** (table `generate_jobs`).

## Hors freeze

UI 3 boutons / loader / poll. Core moteur. Archive / sync.
