# Brief — coller dans le chat **Core**

Le tech lead : **plafonds `max_services` durs au fill** (`core-1`). File tableau Banc close (`master @ 219a33b` ou plus récent). Relis **`contracts/domain/wellbeing.md`** (gagne — section Fill) + `bench.md` Identité (`VERSION`).

`git pull origin master` (doit contenir ce brief + freeze) ; branche **`max-services-hard/core` depuis `master`**.

`/opsx-update wellbeing-model` (fill refuse le dépassement). Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `max-services-hard/core` toi-même**. Message : `feat(core): hard max_services in fill core-1`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. Keep-best / `_attempt_key` / `SEARCH_*` / SAT repos **inchangés**.

## Comportement

- `data/bench/VERSION` = une ligne `core-1`. `engine_ref()` suit.
- Fill : dépasser `max_services` (semaine du shift, même compteur qu’evaluate) = **inéligible**, comme un overlap. Plus le 5ᵉ tie-break derrière les heures.
- Clé absente = pas de plafond. Evaluate / facts `max_evenings` etc. restent des souhaits (sandbox).
- Saint-Cloud : si le solve `optimized` **change**, réécrire `planning` et remonter les stats ; sinon ne pas toucher.

## Tests

`engine_ref() == "core-1"`.  
`run_bench(crafted, marais, minimal)` : **0** fact miss `max_evenings` ; Elsa (`id` `e`) **0** shift `evening`.  
`run_bench(crafted, rivoli, minimal)` : expected 0 interdit (pas de casse we).  
`run_bench(wishes, campus, minimal)` tourne (pas d’exigence de note).  
Atelier : **pas** d’exigence 10 (autre levier).  
`generate_cycle` déterministe inchangé hors fill. Pytest engine / recap / bench verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core max-services-hard pushed @ <sha>`
