# Brief — coller dans le chat **Core**

Le tech lead : **+20 oracles `crafted`**. On **ne retire rien**. Les 30 jeux actuels **bit-à-bit**. File 40 close (`master @ 7675094` ou plus récent). Relis **`contracts/domain/bench.md`** (gagne — tableau + méthode grille d’abord).

`git pull origin master` (doit contenir ce brief + freeze) ; branche **`bench-oracles/core` depuis `master`**.

`/opsx-update bench-datasets`. Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `bench-oracles/core` toi-même**. Message : `feat(core): add twenty crafted bench oracles`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. **Pas** de HTTP. **Pas** d’`engine.py` (fill / SAT / keep-best / `SEARCH_*` **inchangés**). `VERSION` **reste `core-2`**. Les **30** dossiers existants **interdits à l’édition** (y compris les 6 `crafted` déjà là).

## Qualité (non négociable)

Les 23 jeux « forme » du file 40 **ne sont pas** le modèle. Ici : **planning d’abord**.

Pour **chaque** id nouveau :

1. Écrire la grille 14 jours (`expected.json`) qui couvre tous les services ouverts.
2. En déduire fiches / rôles / hours / wellbeing / `typical_week` pour que cette grille soit **légale**.
3. `evaluate(expected)` → **0 interdit**, **0 hours_miss**, **0 below_role**.
4. `cycle_score` globale **≥ 9,5** (viser **10**).

Si un id n’atteint pas 9,5 : **réécrire la grille**, pas baisser la barre.

## Comportement

- `BENCH_CATEGORY_ORDER` **inchangé**.
- **20** dossiers `data/bench/crafted/{id}/` (context + expected) : `bastille` `nation` `sentier` `bourse` `madeleine` `concorde` `tuileries` `palais` `luxembourg` `odeon` `montparnasse` `denfert` `vaugirard` `grenelle` `passy` `auteuil` `monceau` `pigalle` `abbesses` `clichy`.
- Particularité de chaque id = le tableau `bench.md` (contrainte **dans** l’oracle, pas un décor).
- `hours.services` peut inclure `morning`. Plusieurs `types` le même `service_id` si `typical_week` les départage.
- Rôles `level` jusqu’à **6**. Salle only.

## Tests

`list_bench_datasets` = **50**. Les 30 anciens : mêmes bytes / mêmes assignments.  
Chaque paire du freeze : load + `evaluate(expected)` → 0 interdit.  
**26** `crafted` : `cycle_score` expected `global >= 9.5`.  
Les **20** nouveaux : 0 `hours_miss`, 0 `below_role`.  
≥ 4 des 20 avec `morning` ; ≥ 4 avec 2 types le même service ; ≥ 4 avec un rôle `level >= 6`.  
`engine_ref() == "core-2"`. `run_bench(tight, halles, minimal)` vert.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-oracles pushed @ <sha>`
