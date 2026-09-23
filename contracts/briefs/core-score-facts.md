# Brief — coller dans le chat **Core**

Le tech lead : **score facts** — payload typé, plus de FR moteur. File banc-crafted close (`master has bench-crafted landed` @ `6f3eb7a` ou plus récent). Relis **`contracts/domain/score-facts.md`** (gagne) + `score.md` + `cycle-recaps.md` + `exemple-snapshot.md` — tu les suis, tu ne les modifies pas.

`git pull origin master` (doit contenir ce brief) ; branche **`score-facts/core` depuis `master`**.

Pas de nouveau change OpenSpec. Pas d’archive / sync. **Pas** `/opsx-update` obligatoire.

**Process** : tâches + pytest vert → **commit + push `score-facts/core` toi-même**. Message : `feat(core): typed score facts replace warning messages`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Snapshot `data/examples/saint-cloud.json` **oui** (rewrite recap).  
`SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` / `_attempt_key` / `generate_cycle` keep-best **inchangés**.

## Comportement

- `Warning.message` supprimé. `code` (= `kind`) + `payload` dict (catalogue `score-facts.md`). `key()` sans message.
- `evaluate()` : **mêmes misses**, mêmes comptes (keep-best). Zéro FR dans le payload.
- `cycle_recap` : `facts[]` = misses evaluate, puis `role_gap` miss, puis hits (`post_held`, cellules ok, `contract_hours` tenus, `role_gap` hit).
- `RecapCell` : `{ ok, kind, payload }` — plus de `text`.
- `CycleScore` : plus de `resumes`. Notes / poids / globale **inchangés**.
- `refresh_example_snapshot` : plus `planning.warnings` ; `facts` ; Diane payload 30/29/39 ; 17 misses evaluate ; 92 shifts.
- Preview sandbox : impact lists = facts (pas `message`). `contract` / `role_fit` inchangés.
- Employee board : `held` via miss `kind`. Pas les textes panneau.

## Tests

Aucun `message` / `resumes` / `cell.text` sur recap neuf.  
Saint-Cloud : 92 ; 17 misses evaluate ; Diane 30/29/39 ; Théo 660–960 ; wellbeing 10/12 ; 47 below_role.  
Paire < 11 h : payload minutes, pas de jour FR. `empty_post` : weekday + service + clocks minutes + post_level.  
`generate_cycle` déterministe inchangé. `publish_allowed` key() payload.  
Pytest engine / recap / board / hydrate / preview / snapshot verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core score-facts pushed @ <sha>, misses=<n>`
