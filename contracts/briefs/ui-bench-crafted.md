# Brief — coller dans le chat **UI**

Le tech lead : menu admin à plat + tableau **Modèle | Manuel | Delta**. **Attends le land Infra** (`master has bench-crafted landed` Infra). Relis `contracts/domain/bench.md` (section UI).

`git fetch origin` ; si `origin/bench-crafted/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`bench-crafted/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `bench-crafted/ui` toi-même**. Message : `feat(web): admin menu and bench Model Manual Delta v0.29.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, `data/bench/`. Reste `web/`. **`0.29.0`**, note FR : menu admin + banc Modèle / Manuel / Delta.

## Comportement

- `/admin` **et** `/admin/bench` **et** compare : menu **Historique des computes | Banc**. Plus de bouton « Banc » seul ni « ← Admin ». Entrée courante marquée.
- `/admin` = log generate inchangé. `/admin/bench` = banc (liste API, donc les 3 crafted apparaissent tout seuls).
- Tableau : sous chaque effort, 3 sous-colonnes **Modèle** / **Manuel** / **Delta** (`score.global` / `expected_score.global` / `deltas.global`). Tiret si pas de run. Clic → compare.
- Compare : blocs **Modèle** puis **Manuel** (plus « généré » / « oracle »).

## Vérif

Build. Admin : les 2 liens. Banc : 7 lignes, sous-colonnes, crafted visibles. Compare : Modèle / Manuel. Barre **v0.29.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-crafted pushed @ <sha>, v0.29.0`
