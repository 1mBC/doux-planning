# Brief — agent Core · leftover + 11 h wrap + every_two au moins un

Le tech lead : **fenêtres leftover, repos 11 h, un week-end sur deux = au moins un**. Relis `contracts/domain/coverage-rest-weekend.md` (gagne) + table Week-end de `wellbeing.md`. Tu ne modifies pas `contracts/`.

Branche **`cursor/coverage-rest-weekend-2843`** depuis la freeze. **Ne merge pas** `master`.

Pas de nouveau change OpenSpec. Pas d’archive / sync.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic.

**Process** : pytest vert → **commit + push**. Message : `fix(core): leftover windows, wrap rest, at least one weekend off`. Signal le SHA.

## Comportement

- `derive_post_windows` : postes encore live après le dernier événement → `end = max(dernier événement, premier départ)`, jamais `end = start`.
- `_legal_warnings` : `if day_b_raw - day_a > 1: continue` **sans** exception wrap. Toutes les copies vendored.
- `_wellbeing_warnings` `EVERY_TWO` : miss seulement si aucun des deux we n’est entièrement off. Toutes les copies.
- `_build_rest_model` : `even_off + odd_off >= 1`. Toutes les copies.
- `stretch_to_min_shift` et `_rest_between_ok` : intouchés.

## Tests

Scénarios du freeze. Cuisine `remaining ()` inchangée.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core coverage-rest-weekend pushed @ <sha>`
