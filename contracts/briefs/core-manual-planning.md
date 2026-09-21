# Brief — agent Core neuf (cloud) · change **manual-planning**

Le tech lead : **seed grille vide** pour le live. Relis `contracts/domain/manual-planning.md` section Core (gagne). Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/manual-planning-core-2843`** depuis la freeze. **Ne merge pas** `master`.

Nouveau change OpenSpec **`manual-planning`**. Skills → **propose puis `/opsx-apply`**. Pas d’archive / sync.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, Alembic. **Ne pas** ajouter `SearchEffort.MANUEL`. **Ne pas** appeler `generate_cycle` / `generate_for` dans le chemin manuel. Formules `engine.py` / keep-best / `stretch_to_min_shift` intouchées.

**Process** : pytest vert → **commit + push**. Message : `feat(core): seed empty team cycle for manual live`. Signal le SHA.

## Comportement

- `seed_empty_team_cycle(state, team) -> PublishedCycle` : `TeamNotReady` si pas ready ; sinon même squelette que `generate_team` (structures équipe + fiches équipe) avec `assignments=()` et `result=evaluate(draft)` ; écrit `published_cycles[team]`.
- `enter_live_sandbox` / `publish_live_sandbox` / `discard_live_sandbox` **tels quels** (enter après seed).
- Gestes existants seulement.

## Tests

Salle ready, pas de generate → seed : assignments vides, warnings coverage, cuisine `None`. Enter + fill/apply/undo. Pas ready → `TeamNotReady`. Saint-Cloud verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core manual-planning pushed @ <sha>`
