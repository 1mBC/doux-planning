# Contexte restaurant (onboarding live)

Freeze **domaine** pour le resto vide + panneaux. HTTP plus tard (Infra). Generate / publish / sandbox live = tranche suivante, pas celle-ci.

Légal FR = contexte pays `france` (`legal_context_id`), **jamais** copié sur le resto ni les fiches.  
Contrats et indisponibilités = patron (outrent le bien-être). Bien-être = souhaits. `min_shift_hours` défaut **4**. Le moteur continue d’étirer les shifts à ce min à la génération — **ne pas changer** les formules.

Salle et cuisine = équipes **indépendantes**. On peut être prêt à calculer la salle sans la cuisine. Deux cycles / deux sandboxes = plus tard.

## Identité

`RestaurantIdentity.name: str` défaut `""` (le register company ne l’a pas demandé).  
`legal_context_id` défaut `"france"`.

`empty_restaurant(id) -> RestaurantState` : nom `""`, zéro fiche, zéro type, **aucun** service choisi, pas de semaine type, pas de cycle publié. Hydrate Saint-Cloud **inchangé**.

## Échelles et fiches (déjà au domaine — exposer clairement)

- `RoleLadder` par équipe (niveaux + règle de substitution expliquée).
- `Employee` : name, role, team, `contractual_hours_per_week`, `unavailabilities`, `wellbeing`, `min_shift_hours` (4), `invite_token`.
- Une fiche = salle **ou** cuisine.

## Services entreprise

Ensemble **une fois** pour le resto : sous-ensemble de `morning` | `midday` | `evening` (petit-déj / déj / dîner). Vide tant que le panneau services n’est pas rempli.  
`RestaurantHours` actuel exige ≥1 service : le resto vide n’utilise pas encore `hours` pour generate — garder `hours` optionnel (`None`) tant que les services ne sont pas choisis, ou un holder sans service. Ne pas casser Saint-Cloud (`hours` déjà rempli).

## Types (feuilles de vagues)

Un **type** = feuille nommée pour **un** couple (équipe × service) :

```
ServiceType { id, name, team, service_id, arrivals[], departures[] }
```

Vagues = mêmes `ArrivalWave` / `DepartureWave` qu’aujourd’hui (grille 15 min). Ce n’est **pas** un `ServiceStructure.weekdays` rempli à la main : les jours viennent de la semaine type.

## Semaine type → 14 jours

```
TypicalWeekCell { weekday, service_id, type_id: str | null, closed: bool }
TypicalWeek     # 7 jours × services entreprise
```

Cellule ouverte → `type_id` d’un type du bon (team, service) — **par équipe** (deux grilles, ou une grille avec type salle et type cuisine). Cellule fermée → pas de couverture.  
`expand_typical_week(state) -> list[ServiceStructure]` : copie **identiques** semaine A et B (jours 0–6 = 7–13). Les `ServiceStructure.weekdays` produits sont le seul input moteur.

## Prêt à calculer (sans appeler generate)

`team_ready(state, team) -> bool` :

1. échelle de rôles pour l’équipe ;
2. ≥ 1 fiche de cette équipe ;
3. ≥ 1 service entreprise ;
4. ≥ 1 type pour chaque service **ouvert** de cette équipe ;
5. chaque case **ouverte** de la semaine type a un `type_id` valide pour cette équipe.

Salle prête + cuisine incomplète → `team_ready(salle)` vrai, `team_ready(cuisine)` faux.

## Hors freeze

`generate_cycle`, jobs, publish, persist HTTP, panneaux UI, bouton seed Saint-Cloud, second cycle.
