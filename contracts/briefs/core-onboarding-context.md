# Brief — coller dans le chat **Core Engine**

Le tech lead : persist / context. Premier maillon **Python** : resto vide, types nommés, semaine type → 14 j., `team_ready` — **sans** generate. Relis `contracts/domain/restaurant-context.md` (tu le suis, tu ne le modifies pas).

`git fetch origin master` ; master doit contenir l’auth mergée (tokens + `linked_employee_ids` + `invite_token`). Si `Employee.invite_token` / `linked_employee_ids` absents de master → **stop**, remonte au facteur. Branche **`context/core` depuis `master`**. Pas `auth/core`, pas de mega-change generate.

Nouveau change OpenSpec **`onboarding-context`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox / auth. Pas d’archive / sync. Pas de commit.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, `planning.py` preview/fill/undo, `engine.py` formules, FIFO / keep-best / `generate_cycle`, hydrate Saint-Cloud (sauf si un champ nouveau a un défaut inoffensif). Pas d’HTTP.

## Comportement

- `RestaurantIdentity.name` défaut `""`. `legal_context_id` défaut `"france"` (id, pas de copie des règles).
- `empty_restaurant(restaurant_id) -> RestaurantState` : vide, pas de cycle publié.
- Services entreprise : 0..n parmi `morning`/`midday`/`evening`. Resto vide = aucun. `hours` Saint-Cloud inchangé.
- `ServiceType` : id, name, team, service_id, arrivals, departures (vagues existantes).
- `TypicalWeek` + cellules (weekday, service_id, type_id|null, closed). `expand_typical_week` → `ServiceStructure` pour A et B **identiques**.
- `team_ready(state, team) -> bool` selon le freeze (salle peut être prête sans la cuisine).
- Fiches / échelles : réutiliser `Employee` / `RoleLadder` ; `min_shift_hours` défaut 4 ; contrat + unavail = patron ; wellbeing = souhaits. Une fiche, une équipe.
- Mutateurs domaine OK (`set_services`, upsert type, set semaine type, upsert fiche, set name). Pas de persist SQL.

## Tests

Resto vide : pas ready. Ajouter rôles + 1 fiche salle + services + types + semaine ouverte complète → `team_ready(salle)` vrai, cuisine faux. Case ouverte sans type → salle faux. Expand : structures A = B. Saint-Cloud hydrate + pytest existants toujours verts. **Aucun** appel `generate_cycle` dans ce change.

Tâches cochées + pytest vert → stop.
