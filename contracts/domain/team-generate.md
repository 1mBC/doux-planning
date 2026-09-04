# Generate par équipe (cycles live)

Freeze **domaine**. HTTP / jobs / UI = tranches suivantes.  
Salle et cuisine = **deux cycles publiés indépendants**. On génère une équipe prête sans l’autre.

Le moteur existant `generate_cycle(draft, search)` reste **l’unique** solveur. Pas de second algo. Pas de changement FIFO / keep-best / étirement `min_shift` / `SEARCH_SECONDS`.

Saint-Cloud : `RestaurantState.cycle` + sandbox exemple **inchangés**. Ce freeze ajoute `published_cycles` pour le resto **live** (`empty_restaurant`).

## API

```
TeamNotReady          # generate alors que team_ready est faux
generate_team(state, team, search=optimized) -> RestaurantState
```

1. `team_ready(state, team)` faux → `TeamNotReady`. **Aucun** appel `generate_cycle`.
2. `expand_typical_week(state)` → structures.
3. Draft = fiches **de cette équipe** + structures **de cette équipe** + services entreprise + legal `france` (id, pas de copie).
4. `generate_cycle(draft, search)` — `search` = `minimal` | `optimized` | `maximal` (`SearchEffort`).
5. Écrire `published_cycles[team]`. L’autre équipe **intacte**. Regenerer remplace seulement cette équipe.

`published_cycles` : `{ salle: PublishedCycle | None, cuisine: PublishedCycle | None }`.  
Resto vide : les deux `None`. Assignments d’un cycle = uniquement des `employee_id` de cette équipe.

Pas de semaines calendaires, pas de reconciliation, pas de sandbox live, pas de persist SQL dans ce change.

## Tests

Resto vide + salle ready (comme onboarding) : `generate_team(salle, minimal)` → cycle salle non vide, cuisine `None`. `generate_team(cuisine)` → `TeamNotReady`. Second generate salle remplace le cycle salle. Hydrate / preview Saint-Cloud toujours verts. Tests generate : **`minimal` seulement** (pas optimized 30 s).
