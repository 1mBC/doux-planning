# Versions de cycle (3 efforts) + horodatage

Freeze **Infra**. UI 3 rangées / stepper / types = brief UI ensuite.  
**Pas** de Core : `SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` **inchangés** (16 / 320 / `None`+600 s). Maximal = **tous** les calendriers de repos trouvables dans 600 s, puis keep-best. 1 s si peu de calendriers ≠ régression.

## Forme persistée (`published_cycles`)

Plus un seul cycle par équipe. Par équipe :

```
{
  versions: {
    minimal:  Cycle | null,
    optimized: Cycle | null,
    maximal:  Cycle | null
  },
  latest: "minimal"|"optimized"|"maximal"|null
}
```

`Cycle` = assignments + **`facts`** + recap (`stats`, legal/wish, `score` sans resumes — `contracts/domain/score.md` + `score-facts.md`) **plus** `generated_at` ISO (UTC) + `search_effort` + `duration_seconds` (float, temps du solve ; absent sur les vieux slots). **Plus de `warnings[]`.** Vieux JSONB : hydrate Core → `facts`.  
`latest` = effort du `generated_at` le plus récent (égalité : maximal > optimized > minimal).

Maximal : **tous** les calendriers de repos trouvables **et remplis** dans `SEARCH_SECONDS` (600 s wall-clock, keep-best au fil de l’eau). Ce n’est **pas** 600 s d’énumération SAT puis un fill illimité.

Équipe jamais calculée : `versions` tout `null`, `latest` null.

### Coerce lecture (vieux JSONB)

Ancien `{ assignments, warnings, … }` **sans** `versions` → `versions.optimized = cycle`, `generated_at` absent, `latest: "optimized"`. GET n’émet plus l’ancien plat. Pas d’Alembic (JSONB).

## HTTP

`POST /v1/generate` écrit **seulement** `versions[effort]` de cette équipe (recap + `generated_at` + `search_effort` + `duration_seconds`) + recalcule `latest`. L’autre effort / l’autre équipe **intacts**.  
200 / job `done` : `published` = **les deux** équipes au nouveau format.

`GET /v1/cycles` = ce `published`.

`GET /v1/me/planning` : cycle = `versions[latest]` (rien si `latest` null). Salarié **sans** sélecteur.

Sandbox live : `enter` body/query `search_effort` (défaut `latest`). Slot vide → 409 `Aucun cycle publié pour cette équipe.`  
`publish` réécrit **ce** slot (même effort). `generated_at` **inchangé** (c’est la livraison **calcul**, pas l’édition).

## Worker logs (stdout + stderr Railway)

Une ligne claire, horodatée ISO, **flush immédiat** (`PYTHONUNBUFFERED=1`) :

- process start (`pid`, `rss_mb`)
- jobs `running` orphelins → `queued` (`job requeued reason=stale_running`) — crash / OOM
- job pris (`job_id`, team, restaurant_id)
- generate start / **progress ~10 s** (`elapsed_s`, `calendars` remplis, `rss_mb`) / end (durée s, statut done|failed, calendars, rss)
- `error` si failed

Côté **web** (uvicorn) : POST maximal 202 (`job_id`) ; GET job `done`/`failed`.

## Hors freeze

UI sélecteur / chrome / types. Core `engine.py`. Archive / sync.
