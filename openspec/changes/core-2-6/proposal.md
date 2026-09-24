# Proposal

## Why

Les repos de week-end s’empilent sur la même semaine, et le remplissage laisse un poste vide ou le donne à quelqu’un déjà au-dessus de son contrat alors qu’une personne disponible, de niveau suffisant, est encore en dessous.

## What Changes

- Nouveau moteur `core-2.6`, copie de `core-2`.
- Les week-ends off (un sur deux, paire, impaire) sont répartis : les deux semaines diffèrent d’au plus un repos.
- On ne dépasse un contrat que si personne d’autre de disponible, de niveau suffisant, et sous son contrat, ne peut prendre le poste.
- À horaire égal dans ce vivier, on prend le plus bas rapport heures déjà faites / contrat, puis le niveau le plus proche. Un transfert ensuite rapproche les gens de même niveau et de même contrat.
- Le repos de semaine se pose sur le jour qui laisse le plus de monde. L’horaire posé est celui de la fenêtre du service type, même si elle est plus courte que le minimum de shift et que personne ne tient ce minimum.
- `core-2.6` entre dans le registre après `core-2.5`. Le dernier reste `mix-0`.

## Capabilities

### New Capabilities

- `engine-core-2-6`: week-ends répartis, contrat, équilibre, repos de semaine, fenêtre exacte.

### Modified Capabilities

- Aucune.

## Impact

- Core : `engines/core_2_6.py`, `engines/registry.py`, tests du moteur.
- Pas de route, pas d’écran, pas de migration.
- `mix-0` n’appelle pas `core-2.6`.

## Hors-scope

- Pas d’entrée dans `mix-0`.
- Pas d’archive des autres moteurs, pas de rebase de `iter-0`, pas de retrait de `core-5`.
- Pas de blocs de jours, pas de nouvelle note de profil.

## Critère de complet

- `core-2.6` est dans le registre, après `core-2.5`. Le repli reste `mix-0`.
- Les week-ends un sur deux sont répartis, les souhaits pair et impair restent verrouillés.
- Un contrat n’est dépassé que si personne d’autre, disponible et sous contrat, ne peut prendre le poste.
- L’horaire posé est celui de la fenêtre, même plus court que le minimum.
