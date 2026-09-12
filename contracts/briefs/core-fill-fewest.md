# Brief — coller dans le chat **Core**

Le tech lead : fill **`fewest`** — créneaux au moins de monde d’abord (`core-2`). File 38 close (`master @ 62eb9de` ou plus récent). Relis **`contracts/domain/wellbeing.md`** (gagne — section Fill créneaux rares) + `bench.md` Identité.

`git pull origin master` (doit contenir ce brief + freeze) ; branche **`fill-fewest/core` depuis `master`**.

`/opsx-update wellbeing-model`. Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `fill-fewest/core` toi-même**. Message : `feat(core): fill fewest-eligible windows first core-2`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Keep-best / `_attempt_key` / `SEARCH_*` / SAT / `max_services` dur **inchangés**.  
**Une** stratégie dans cette file (`fewest`). Pas `weekend-eve`, pas `eve-first`.

## Comportement

- `data/bench/VERSION` = une ligne `core-2`. `engine_ref()` suit.
- `_fill_assignments` et `_repair_holes` : même ordre **fewest** (wellbeing.md). Comptage éligibles **statique** (board vide + repos + indispos + plafonds durs + légal).
- Saint-Cloud : si le solve `optimized` **change**, réécrire `planning` et remonter les stats ; sinon ne pas toucher.

## Tests

`engine_ref() == "core-2"`.  
`run_bench(crafted, atelier, minimal)` : **moins de 4** `empty_post` samedi soir (core-1 en a 4). Pas d’exigence globale 10.  
`run_bench(crafted, marais, minimal)` : Elsa (`id` `e`) **0** shift `evening` (pas de régression `core-1`).  
`run_bench(crafted, rivoli, minimal)` : expected 0 interdit.  
`run_bench(wishes, campus, minimal)` tourne.  
Pytest engine / recap / bench verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core fill-fewest pushed @ <sha>`
