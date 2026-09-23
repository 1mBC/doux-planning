# Brief — coller dans le chat **Core**

Le tech lead : **banc = même recap que le live** (facts miss+hit Modèle **et** Manuel). File score-facts close (`master has score-facts landed` @ `29c3794` ou plus récent). Relis **`contracts/domain/bench.md`** (gagne, section Recap unique) + `score-facts.md`.

`git pull origin master` (doit contenir ce brief) ; branche **`bench-pack/core` depuis `master`**.

Pas de nouveau change OpenSpec. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-pack/core` toi-même**. Message : `feat(core): bench recap from draft for model and expected`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Keep-best / `SEARCH_*` / `_attempt_key` **inchangés**.

## Comportement

- Extraire `cycle_recap_from_draft(draft, result) -> CycleRecap` (stats, legal/wish, `facts` complets, `score`). `cycle_recap(state, team)` **l’appelle** — pas une 2ᵉ formule.
- `run_bench` : recap sur le generate **et** sur `expected` (`evaluate` + recap, pas de 2ᵉ solve).
- `BenchOutcome.facts` / `expected_facts` = ces `recap.facts` (hits inclus, pas seulement evaluate misses).
- Zéro écriture `published_cycles`.

## Tests

`run_bench(tight, halles, minimal)` : `expected` 0 interdit ; `facts` **et** `expected_facts` non vides ; au moins un hit (`post_held` ou `role_gap` polarity hit) d’un côté.  
`cycle_recap_from_draft` sur un cycle live-like = mêmes `facts` que `cycle_recap` si publié identique.  
`generate_cycle` déterministe inchangé. Pytest engine / recap / bench verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-pack pushed @ <sha>`
