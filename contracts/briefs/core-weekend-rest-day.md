# Brief — coller dans le chat **Core Engine**

Le tech lead : case bien-être **au moins un repos par week-end**. Relis `contracts/domain/wellbeing.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; master doit contenir **`e1063d4`** (`contracts: weekend_rest_day`). Branche **`weekend-rest/core` depuis `master`**.

Nouveau change OpenSpec **`weekend-rest-day`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` wellbeing-model / seed / sandbox. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `weekend-rest/core` toi-même**. Message : `feat(core): weekend_rest_day wellbeing`. Pas de PR master. Signal le SHA. L’orchestrateur landera plus tard (plus de « land » Bastien).

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. Ne pas réécrire le planning Saint-Cloud (clé absente = `false`, stats 92 / 17 / 10/12 **inchangés**). Ancienne clé liste `at_least_one_weekend_rest_day` reste **refusée**.

## Comportement

- `Wellbeing.weekend_rest_day: bool` (défaut false), **cumulable** avec `weekend` radio.
- Warning + solveur : **chaque** semaine, samedi **ou** dimanche off. Jour fermé = repos.
- `employee_board` : `{ kind: "weekend_rest_day", held }` si la case est posée.
- Hydrate : bool objet ; défaut false si clé absente.

## Tests

Dimanche fermé + case cochée → tenu sans autre repos we. Dimanche ouvert + sam et dim travaillés → warning `weekend_rest_day`. Cumul avec `weekend: even`. Pytest domaine / engine / board / hydrate verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core weekend-rest pushed @ <sha>`
