# Sandbox live (cycle publié d’une équipe)

Freeze **domaine**. HTTP / UI = ensuite.  
Le joujou Saint-Cloud (`state.sandbox`, `hydrate`, `/v1/sandbox/*`) **ne change pas**.

Après `generate_team`, le patron édite **ce** cycle (retune / replace / swap / fill déjà là). Salle et cuisine = **deux** brouillons indépendants.

Réutiliser `preview_retune` / `preview_replace` / `preview_swap` / `preview_fill`, `apply_proposal`, `undo_sandbox`. **Pas** de nouveau geste. **Pas** de changement FIFO / keep-best / formules.

## API

```
NoPublishedCycle
enter_live_sandbox(state, team) -> Sandbox
discard_live_sandbox(state, team) -> None
publish_live_sandbox(state, team) -> RestaurantState
```

- `published_cycles[team]` absent → `NoPublishedCycle`. Pas d’enter.
- Enter : brouillon = draft + result du cycle publié. Ré-enter = même brouillon (historique conservé).
- `live_sandboxes[team]` indépendant de l’autre équipe et de `state.sandbox` Saint-Cloud.
- Discard : jette le brouillon de **cette** équipe ; le publié reste. Ré-enter = publié intact.
- Publish : `published_cycles[team] =` draft courant (assignments + warnings). Pas de semaines / reconciliation. L’autre cycle intact.
- Preview / apply / undo : opèrent sur `live_sandboxes[team]` (passer `team` ou router le store). Saint-Cloud continue d’utiliser `state.sandbox`.

## Tests

`empty_restaurant` + salle ready + `generate_team(..., minimal)` → enter salle OK ; enter cuisine → `NoPublishedCycle`. Retune + apply + undo comme les tests preview existants, **sur le live salle**. Discard puis enter : assignments = publié, history vide. Publish : `GET` conceptuel = nouveau publié ; l’autre équipe `None`. Hydrate / `/`-tests Saint-Cloud inchangés. **Pas** de `generate_cycle` hors le setup `generate_team` minimal.

## Hors freeze

HTTP, persist, UI Mode édition live, jobs, `/me/shifts`, lock du joujou public.
