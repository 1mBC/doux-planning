# Brief — coller dans le chat **Core**

Le tech lead : **banc de jeux** — charger `data/bench/`, `run_bench` isolé, scores généré vs oracle. File score-gauges close (`master has score-gauges landed` @ `8f3f3f9` ou plus récent). Relis `contracts/domain/bench.md` — tu le suis, tu ne le modifies pas.

`git pull origin master` (doit contenir ce brief + `data/bench/`) ; branche **`bench/core` depuis `master`**.

Nouveau change OpenSpec **`bench-datasets`**. Skills → **propose puis `/opsx-apply`**. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench/core` toi-même**. Message : `feat(core): load bench datasets and run isolated generate`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `saint-cloud.json`, `data/bench/**` (lecture seule). **Pas** de HTTP.  
`SEARCH_*` / `_attempt_key` / `generate_cycle` keep-best **inchangés**.

## Comportement

- `list_bench_datasets` / `load_bench_dataset` / `run_bench` selon `bench.md`.
- Load = contexte live (`set_services`, ladder, types, typical_week **dérivée**, fiches). `team_ready(salle)` vrai.
- `run_bench` : copie jetable + `generate_cycle` + `cycle_score` ×2 (généré / expected) + `deltas`. **Zéro** écriture `published_cycles`.
- `data/bench/VERSION` : Core n’a pas à le persister (Infra). Jeu incomplet → omit.

## Tests

4 jeux. Load halles → ready salle, pas cuisine. `evaluate` expected des 4 → 0 interdit.  
`run_bench(tight, halles, minimal)` → `score` + `expected_score` + `deltas`.  
State `empty_restaurant` + fiches **identique** avant/après `run_bench`. Pytest engine / recap verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench pushed @ <sha>`
