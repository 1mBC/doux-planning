# Grille employé (cycle publié live)

Freeze **domaine**. HTTP / UI = ensuite.  
Produit : le salarié voit **toute** la grille de **son** équipe (cycle publié), ses lignes mises en avant (couleur = UI). Il **voit** contrat + indispos + souhaits, il **n’édite** pas. Jamais le brouillon `live_sandboxes`.

`employee_view` actuel (shifts **à soi** seulement, Saint-Cloud `cycle` / weeks) **reste** pour ses tests. Ici : nouvelle API live.

Pas de `legal_rows` / `wish_rows` snapshot Saint-Cloud recopiés. Souhaits = prefs de la fiche + warnings `souhait` du `EngineResult` **déjà** sur `published_cycles[team]`. Pas de second solve, pas de `generate_cycle`.

## API

```
UnknownEmployee
employee_board(state, employee_id) -> EmployeeBoard
```

`EmployeeBoard` :

- `employee_id`, `team` (salle **ou** cuisine de la fiche)
- `assignments` : **tous** les shifts de `published_cycles[team]` (pas seulement les siens). `None` publié → tuple vide (pas d’erreur).
- `contract` : `{ weekly, assigned, ok }` — `weekly` = `contractual_hours_per_week` ; `assigned` = somme `duration_hours` de **cet** employé sur le cycle (0 si pas de publié) ; `ok` si chaque semaine du cycle est dans la tolérance contrat déjà au moteur (`CONTRACT_HOUR_TOLERANCE`) **ou**, si plus simple et documenté, `ok` = aucune warning contrat pour cet `employee_id` sur le result publié.
- `wishes` / `unavailabilities` : forme et mapping **`contracts/domain/wellbeing.md`** (gagne). Plus de `{ key: WellbeingPreference }`.

Fiche inconnue → `UnknownEmployee`. Ne pas lire `live_sandboxes`. Ne pas filtrer les assignments des collègues.

## Tests

Salle générée (minimal) + fiche A avec un souhait : board A a **tous** les assignments salle ; `held` faux s’il existe une warning de ce code pour A, vrai sinon. Cuisine sans cycle : assignments `()`. Enter live + cran **non publié** : board encore = publié. Pytest Saint-Cloud / `employee_view` verts.

## Hors freeze

HTTP `/v1/me/planning`, UI couleur, edit contraintes salarié, legal_rows live.
