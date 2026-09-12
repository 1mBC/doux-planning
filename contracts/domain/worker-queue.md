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
Un process = un solve. N replicas ⇒ N solves concurrents, même `engine_ref`.

Claim : `queued` → `running` + `heartbeat_at = now()`.

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

Alembic : ajouter `heartbeat_at` aux deux tables. Backfill `heartbeat_at = now()` pour les `running` existants (ils ont 180 s de plus, pas un steal immédiat au deploy).

## Dédup banc

Index unique partiel :

```
UNIQUE (category, dataset_id, search_effort)
  WHERE status IN ('queued', 'running')
```

`POST /v1/admin/bench/run` : si un job `queued`/`running` existe déjà pour cette clé → **renvoyer son `job_id`**, pas de 2ᵉ ligne.  
Deux clics « Lancer les 50 Maximal » = **50** jobs, pas 100.

`done` / `failed` libèrent la clé : relancer = nouveau job (nouveau run).

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
- 2× enqueue même `(category, id, effort)` tant que `queued` → **même** `job_id`.
- Generate 409 maximal déjà en cours **inchangé**.
- Pas d’attente 600 s.

## Hors freeze

Un worker par SHA (`core-0` / `core-1` sur de nouveaux JSON). Redis. HTTP interne worker. Cuisine banc.
