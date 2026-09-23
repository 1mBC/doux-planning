# File jobs (workers N replicas)

Freeze **Infra**. La file **est** Postgres. Pas de Redis, pas d’HTTP worker, pas de queue externe.

Web et workers = **même image**, **même `DATABASE_URL`**.  
Web : INSERT `queued`. **Ne solve pas** Maximal / banc Maximal.  
Worker : boucle, **un job à la fois par process**. Scale = **replicas du même service** (même commit). **Pas** un worker par SHA historique.

Jobs resto (`generate_jobs`) et jobs banc (`bench_jobs`) : **deux tables**, même pile, **pas** de 409 croisé.

## Comment ça marche

```
navigateur → web (FastAPI)
               │  INSERT generate_jobs / bench_jobs  status=queued
               ▼
            Postgres
               ▲
     worker-1, worker-2, … worker-N
       SELECT … FOR UPDATE SKIP LOCKED
       → running + heartbeat
       → solve dans CE process (catalogue = image data/bench/)
       → persist published_cycles / bench_runs
       → done | failed
```

Le worker **n’écoute rien**. Il poll la DB. L’UI poll les `job_id` renvoyés par le 202.

## Boucle

Chaque replica, en boucle :

1. Reclaim **stale-by-heartbeat** (les deux tables) — **pas** tous les `running`.
2. `tick_generate_job` — FIFO `created_at`, un `queued`, `SKIP LOCKED`.
3. sinon `tick_bench_job` — même règle.
4. sinon sleep 1 s.

Resto Maximal **avant** le banc (un tick resto si un `queued` existe).  
Un process = un solve. N replicas ⇒ N solves concurrents. Job banc porte **`engine_ref`** (moteur vendored ou live) — plus « forcément VERSION ».

Claim : `queued` → `running` + `heartbeat_at = now()` + **`started_at = now()`**.

## Heartbeat

Colonne `heartbeat_at` timestamptz **nullable** sur `generate_jobs` **et** `bench_jobs`.

Pendant le solve : **toutes les 10 s** `UPDATE heartbeat_at = now()` (thread, generate **et** banc).  
Log generate inchangé (`calendars`, `rss_mb`) ; banc : au moins `job_id` + elapsed.

Constante : `STALE_HEARTBEAT_SECONDS = 180`.

## Reclaim

Un job `running` est stale ssi `heartbeat_at IS NULL OR heartbeat_at < now() - 180s`.  
Stale → `queued`, `error = null`. **Uniquement** ceux-là.

**Interdit** : au start, remettre **tous** les `running` en `queued` (un replica neuf volerait les Maximal en cours).

Reclaim au start **et** à chaque tour de boucle (requête indexée, pas cher).

Alembic **cette file** : `bench_runs.trace` JSONB ; `bench_jobs.engine_ref`, `batch_id`, `started_at` ; unique partiel 4-clés (drop l’ancien 3-clés). `heartbeat_at` **déjà** landed.

## Dédup banc

Index unique partiel :

```
UNIQUE (category, dataset_id, search_effort, engine_ref)
  WHERE status IN ('queued', 'running')
```

`engine_ref` **obligatoire** sur chaque `bench_jobs` (défaut VERSION à l’enqueue habituel).  
Enqueue : si un job `queued`/`running` existe déjà pour cette clé → **renvoyer son `job_id`**, pas de 2ᵉ ligne.  
`core-2` Maximal et `core-3` Maximal du même jeu : **deux** jobs OK.

`done` / `failed` libèrent la clé.

## Batch

Colonne `batch_id` (string) sur `bench_jobs`. Un POST async (`all` / `category` / `dataset` Maximal / `gaps`) = **un** `batch_id` partagé.  
`started_at` timestamptz null tant que `queued`.

Progress / eta : `contracts/domain/bench.md` GET batches.

Generate resto : 409 si `queued`/`running` même company+team — **inchangé**.

## Logs

Chaque `taken` / `end` : `worker=<hostname>:<pid>`. Pas de colonne `claimed_by` obligatoire.

## Railway / Compose

Service **worker** : replicas **N** (slider Railway, ou `docker compose up --scale worker=N`).  
Même start `python -u -m doux_planning.api.worker`. **Pas** d’Alembic dans le worker.  
Service **web** : ne lance **pas** la boucle worker. Replicas web OK (stateless) ; la file reste les workers.

## Tests (stub, 0 s)

- Deux ticks concurrents (threads) sur 2 `queued` → 2 jobs **distincts**, aucun steal.
- `running` + `heartbeat_at` frais → reclaim **0**.
- `running` + heartbeat trop vieux → reclaim **1**, status `queued`.
- Start worker + job `running` frais → **pas** requeue.
- 2× enqueue même `(category, id, effort, engine_ref)` tant que `queued` → **même** `job_id`.
- 2 refs différents → 2 jobs.
- POST gaps stub → un `batch_id`, jobs = nombre de trous ; GET batch `pct` / `eta_max_seconds`.
- Generate 409 maximal déjà en cours **inchangé**.
- Pas d’attente 600 s.

## Hors freeze

Redis. HTTP interne worker. Cuisine banc. Un process par SHA git.
