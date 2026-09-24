# Moteur `core-2.6`

Freeze **Core**. Module **nouveau** `engines/core_2_6.py`, copie de `core_2.py`.

`engine_ref` = `core-2.6`. Keep-best / `_attempt_key` **inchangés**. Catalogue 50 **inchangé**. Pas de seeds de créneaux. `mix-0` ne l’appelle pas.

## Week-ends

Semaine A = jours 5 et 6. Semaine B = jours 12 et 13. Off = aucun shift sur les deux jours. Un jour fermé compte off.

- `even` : off A, et au moins un shift en B.
- `odd` : off B, et au moins un shift en A.
- `every_two` : exactement un des deux. Tri par id. On remplit le côté le moins chargé, A si égalité, pour minimiser `|compte A − compte B|`.
- Pas de souhait : aucun week-end forcé, pas compté dans les effectifs.

Les verrous `even` / `odd` ne sont pas cassés pour forcer l’écart ≤ 1. Contraintes dures du modèle de repos. L’énumération (16 / 320 / sans plafond) et le keep-best restent. Infaisable avec l’équilibrage : on relâche seulement l’équilibrage, on garde les souhaits individuels, puis le repli de `core-2`.

## Repos de semaine

Après les week-ends, personnes triées par id. Pour chaque repos encore dû (2 par semaine, moins les jours déjà off) : jours ouverts qui ne sont pas un week-end à travailler. Surplus = min sur les services de (collègues pas off, niveau suffisant pour au moins un poste) − (nombre de postes). On pose le repos au surplus max, même si ce max est négatif. Ce calendrier est évalué avec ceux de l’énumération.

## Choix d’un poste

Filtres durs de `core-2` : niveau ≥ poste, pas off, pas de chevauchement, 11 h, plafonds soirées et coupures, indispo, plafonds jour et semaine. Pas le veto « un collègue quelconque est sous son contrat ».

```
fit = disponibles dont durée(fenêtre) ≥ minimum du service
pool = fit si non vide, sinon tous les disponibles
choix = membres de pool avec heures_semaine < contrat, sinon pool
tri = (heures_semaine / contrat, niveau − niveau_poste, id)
horaire = début et fin de la fenêtre
```

Pas d’étirement. Personne dans `choix` : le poste reste vide.

## Transfert

Après le fill, par semaine, par groupe (même niveau, même contrat) d’au moins 2 :

Tant que max − min > 0,5 h, déplacer un shift du plus chargé vers le moins chargé si le receveur passe les filtres sur cet horaire et que ses heures après coup restent ≤ celles du donneur. On garde le transfert qui réduit le plus l’écart. Sinon stop.

## Registre

`list_engine_refs()` insère `"core-2.6"` immédiatement après `"core-2.5"`. Dernier = `"mix-0"`.

## Tests

- 4 × `every_two`, aucun `even` / `odd` → 2 off A et 2 off B.
- 1 `even`, 1 `odd`, 2 `every_two` → verrous respectés, écart ≤ 1.
- Sans souhait week-end → peut travailler les deux.
- Deux éligibles, un seul sous contrat → celui sous contrat.
- Un seul éligible au-dessus du contrat → il prend le poste.
- Même niveau et même contrat, rapport plus bas → il prend le poste.
- Écart > 0,5 h et transfert légal → le gap baisse, receveur ≤ donneur.
- Deux jours possibles pour un repos → celui au surplus le plus haut.
- Au moins un minimum ≤ fenêtre → horaire = fenêtre, titulaire dans ce groupe.
- Tous les minimums > fenêtre → horaire = fenêtre quand même, pas d’allongement.
- `mix-0` n’a pas `core-2.6` dans `MIX0_EXPERTS`.

## Hors freeze

Blocs de 3 jours. Note dispo / occupation / niveau / écart au minimum. Entrée dans `mix-0`. Archive des autres moteurs.
