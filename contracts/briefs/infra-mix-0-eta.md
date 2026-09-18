# Brief — coller dans le chat **Infra** (après land Core)

Le tech lead : ETA bench pour **`mix-0`**. Freeze `engine-mix-0.md` (section Infra).

`git pull origin master` ; branche **depuis `master`** (Core mix-0 déjà landé).

**Ne pas toucher** `web/`, `contracts/`, Core hors `api/`.

**Process** : commit + push. Titre : `feat(api): mix-0 bench ETA is sum of experts`. Pas de PR master. Signal le SHA.

## Comportement

`src/doux_planning/api/bench.py` `_effort_cap(job)` (ou équivalent qui lit `search_effort` **et** `engine_ref`) :

Si `job.engine_ref == "mix-0"` :

- `minimal` / `optimized` → `4 * SEARCH_SECONDS[effort]` (`MIX0_EXPERTS` = 4)
- `maximal` → `SEARCH_SECONDS[maximal]` (600)

Sinon inchangé.

Ça alimente `eta_max_seconds` du batch. Sans ça, mix-0 optimized affiche ~30 s alors qu’il tourne ~2 min.

Pas d’autre route. Pas d’Alembic.

## Tests

- job mix-0 optimized : cap 120 s
- job core-2 optimized : cap 30 s (pas de régression)
- pytest vert
