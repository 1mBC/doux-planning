# Design

## Context

`core-2` énumère des calendriers de repos (16 en minimal, 320 en optimized, sans plafond en maximal), remplit chaque calendrier, et garde le meilleur `_attempt_key`. Il n’utilise pas les seeds de créneaux de `core-3`. Voir proposal.md pour le besoin.

## Goals / Non-Goals

**Goals:**

- Copier `core_2.py` vers `core_2_6.py` et n’y changer que les cinq règles du spec.
- Garder l’énumération des calendriers et le keep-best.

**Non-Goals:**

- Blocs de jours consécutifs.
- Note « dispo, occupation, niveau, écart au minimum ».
- Étirement du shift jusqu’au minimum.
- Ajouter `core-2.6` dans `MIX0_EXPERTS`.
- Archiver des moteurs, rebaser `iter-0`, retirer `core-5`.

## Decisions

**Base.** `engines/core_2_6.py` est une copie de `core_2.py`. Le registre l’insère après `core-2.5`. Il n’entre pas dans `_SEEDS_ENGINES` ni `_CUSTOM_TRACE_ENGINES`. Le trace reste celui de `core-2` (`seeder="empty"`).

**Week-ends, en dur dans le modèle de repos.** Semaine A = jours 5 et 6, semaine B = jours 12 et 13. Off = aucun shift ces deux jours. `even` verrouille A et exige au moins un shift en B. `odd` verrouille B et exige au moins un shift en A. `every_two` reçoit exactement un côté. On attribue les `every_two` (tri par id) au côté le plus léger, A en cas d’égalité, jusqu’à minimiser `|compte A − compte B|`. Si les verrous `even` / `odd` empêchent l’écart ≤ 1, on ne les casse pas. Quelqu’un sans souhait n’est pas compté. Un dimanche fermé compte off ; « travailler le week-end » veut alors dire travailler le samedi.

**Plusieurs calendriers.** Ces contraintes de week-end sont ajoutées au modèle déjà énuméré. On évalue aussi le calendrier glouton de la règle de surplus. Keep-best inchangé. Si le modèle avec la répartition est infaisable, on relâche seulement l’équilibrage et on garde les souhaits individuels (`every_two` au moins un, `even` / `odd` exacts), puis le repli déjà présent dans `core-2`.

**Surplus.** Après les week-ends fixés, pour chaque personne (tri par id) et chaque repos encore dû : jours ouverts hors week-end qu’elle doit travailler. Surplus = minimum, sur les services du jour, de (collègues pas déjà off, capables de tenir au moins un poste) − (nombre de postes). On pose le repos sur le surplus max. Tous négatifs : on le pose quand même.

**Choix d’un poste.** Les filtres durs de `core-2` restent (niveau, repos, chevauchement, 11 h, plafonds soirées et coupures, indispo, plafonds du jour et de la semaine). Le veto « un collègue est sous son contrat » disparaît. Le minimum de shift ne décale plus l’heure.

```
fit = disponibles dont la fenêtre dure au moins leur minimum
pool = fit s'il est non vide, sinon tous les disponibles
choix = ceux de pool strictement sous leur contrat, sinon pool
tri = (heures_semaine / contrat, niveau − niveau_du_poste, id)
horaire = début et fin de la fenêtre
```

**Transfert.** Après le remplissage, par semaine et par groupe (niveau, contrat) d’au moins deux personnes : tant que l’écart dépasse 0,5 h, déplacer un shift du plus chargé vers le moins chargé si le receveur peut le tenir (mêmes filtres, fenêtre déjà posée) et que ses heures restent ≤ celles du donneur. On prend le transfert qui réduit le plus l’écart. Sinon on s’arrête.

## Risks / Trade-offs

- [Le surplus compte « capable d’au moins un poste », pas chaque niveau] → un jour peut sembler couvert alors qu’un niveau 3 n’a personne. Le keep-best peut alors préférer un autre calendrier plus rempli.
- [Keep-best peut écarter le calendrier au meilleur surplus] → seulement s’il laisse plus de trous ou un moins bon `_attempt_key`. C’est le comportement voulu de `core-2`.
- [Un shift plus court que le minimum n’allume pas d’alerte] → la note ne mesure pas ce minimum. Hors de ce change.
