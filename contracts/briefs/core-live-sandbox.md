# Brief — coller dans le chat **Core Engine**

Le tech lead : sandbox live. Premier maillon **Python** : enter / discard / publish sur `published_cycles[team]`, deux brouillons. Relis `contracts/domain/live-sandbox.md` (tu le suis, tu ne le modifies pas).

`git fetch origin master` ; master doit contenir generate mergé (`generate_team`, `published_cycles`, `TeamNotReady`). Si `generate_team` manque → **stop**, remonte au facteur. Branche **`live/core` depuis `master`**. Pas `generate/core`.

Nouveau change OpenSpec **`live-sandbox`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox joujou / team-generate / onboarding. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `engine.py` formules, preview_* (sauf les router vers le brouillon live), hydrate Saint-Cloud, `state.sandbox` joujou. Pas d’HTTP.

## Comportement

- `live_sandboxes[team]`. `NoPublishedCycle` si pas de cycle publié.
- Enter / discard / publish selon le freeze. Preview/apply/undo **existants** sur ce brouillon.
- Publish écrit seulement `published_cycles[team]`. Pas de reconciliation semaines.

## Tests

Salle générée (minimal) → enter + cran + undo + discard restaure le publié ; publish met à jour salle seulement ; cuisine sans cycle → `NoPublishedCycle`. Pytest Saint-Cloud verts.

Tâches cochées + pytest vert → stop.
