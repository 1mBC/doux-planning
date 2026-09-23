# Brief — agent Core · note banc = evaluate live

Le tech lead : **la note persistée d’un run banc = la même que la page « voir »**. Relis `contracts/domain/bench-score-live.md` (gagne) + le paragraphe Last-run / score de `bench.md`. Tu ne modifies pas `contracts/`.

Branche **`cursor/bench-score-live-core-2843`** depuis `master` (freeze file 76 déjà dessus). **Ne merge pas** `master`.

OpenSpec change **`bench-score-live`** déjà écrit. Coche les tâches Core. Pas d’archive / sync. Pas de nouveau change.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic, `engine.py` formules, leftover, copies vendored evaluate, picker mix-0.

**Process** : pytest vert → **commit + push**. Message : `fix(core): bench run score from live evaluate`. Signal le SHA. Pas de PR master.

## Comportement

`run_bench_on` dans `src/doux_planning/bench.py` (déjà importe `evaluate`) :

Après `generate_for(...)` :

```
model_draft = draft.with_assignments(result.assignments)
scored = evaluate(model_draft)
recap = cycle_recap_from_draft(model_draft, scored)
```

`outcome.score` / `facts` / `warnings` viennent de `recap` / `scored`.  
`outcome.assignments` = `result.assignments` (générés).  
`outcome.engine_ref` = ref demandée.  
Côté oracle : déjà `evaluate` — ne pas changer.  
`published_cycles` : toujours interdit d’écrire.

Ne **pas** rescoring dans mix-0 pour le picker. Ne **pas** toucher Infra `persist_bench_outcome` / `_cycle_slice` / `GET /versions`.

## Tests

- `run_bench_on(..., engine_ref="core-2")` et `engine_ref="mix-0"` sur un jeu catalogue `minimal` : `outcome.score.global_score` == recap live `evaluate` des `outcome.assignments`.
- Pytest `test_bench.py` / engine existants verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core bench-score-live pushed @ <sha>`
