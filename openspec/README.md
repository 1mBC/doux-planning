# Lire OpenSpec

Trois endroits. Ils ne disent pas la même chose.

**Le produit courant, pour les formes, est `contracts/`.** En cas de désaccord de forme, ce dossier gagne.

**`openspec/specs/` est le socle du 4 septembre 2026.** Quatre fichiers : équipes et fiches, structures de service, cycle de 14 jours, moteur. Les changes livrés ensuite ont été archivés sans recopier leurs deltas ici. Une exigence de ces fichiers peut donc décrire un comportement déjà dépassé.

Exemples dépassés, à ne pas reprendre tels quels :

- Le bac à sable n'a plus une seule cible. Il y en a un par équipe.
- Le minimum de créneau n'est plus un seul nombre par fiche. Il est par service.
- Le bien-être n'est plus un sac de drapeaux. La fiche a une structure.
- Le moteur courant n'est plus un fichier `VERSION`. Deux choix sont en base, banc et client. Sans choix valable, c'est le dernier nom du registre.

**`openspec/changes/archive/` garde l'historique.** Chaque dossier est un change livré, avec ses deltas d'époque. Ce n'est pas une spec fusionnée. On ne rejoue pas cet historique dans `openspec/specs/` dans le désordre.

**`openspec/changes/bench-engine-choice/` est le seul change actif.** Il est sur `master` pour l'essai Railway. On ne l'archive que lorsque le parcours est validé.

Un prochain passage pourra réécrire `openspec/specs/` au présent, une capacité à la fois, à partir des contrats. Pas en fusionnant les 34 archives d'un coup.
