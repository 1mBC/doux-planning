# Brief — coller dans le chat **Core Engine**

Le tech lead : generate / cycles. Premier maillon **Python** : `generate_team` wrappe `generate_cycle`, deux cycles publiés. Relis `contracts/domain/team-generate.md` (tu le suis, tu ne le modifies pas).

`git fetch origin master` ; master doit contenir le contexte mergé (`empty_restaurant`, `team_ready`, `expand_typical_week`). Si ces symboles manquent → **stop**, remonte au facteur. Branche **`generate/core` depuis `master`**. Pas `context/core`.

Nouveau change OpenSpec **`team-generate`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox / onboarding / auth. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `engine.py` formules / FIFO / keep-best / `SEARCH_SECONDS`, preview/fill, hydrate Saint-Cloud (sauf défaut inoffensif). Pas d’HTTP. Pas de jobs.

## Comportement

- `published_cycles` salle / cuisine sur le state live. Saint-Cloud `cycle` inchangé.
- `generate_team(state, team, search)` : `team_ready` faux → `TeamNotReady` sans solve ; sinon expand + draft **une** équipe + `generate_cycle`. Autre cycle intact.
- `search` = `SearchEffort` (défaut optimized). Tests = **minimal**.

## Tests

Salle ready → generate minimal : assignments salle only, cuisine None. Cuisine not ready → `TeamNotReady`. Re-generate salle remplace salle. Pytest existants verts.

Tâches cochées + pytest vert → stop.
