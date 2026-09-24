# Lire OpenSpec

Deux vérités, un chantier, une archive.

```
contracts/          formes courantes (routes, JSON). Gagne en cas de désaccord de forme.
openspec/specs/     comportement que l'on tient pour vrai, après copie du delta.
openspec/changes/   le chantier en cours. Un seul à la fois. Vide quand rien n'est ouvert.
openspec/changes/archive/   chantiers finis. On ne les rouvre pas pour coder.
```

## Boucle

1. On ouvre un change. Il décrit le besoin, les cas limites, et un delta : ce qui s'ajoute ou change dans les specs.
2. On le réalise. Le change reste ouvert pendant l'essai sur Railway.
3. Tu dis que c'est validé. On copie le delta dans `openspec/specs/`, on vérifie, puis on déplace le dossier dans l'archive.

Le prochain change part des specs à jour et des contrats. Il ne réécrit pas l'archive.

## État

Cinq specs dans `openspec/specs/`.

- `bench-engine-choice` est à jour. Copiée le 24 septembre 2026, à la validation.
- Les quatre autres datent du 4 septembre 2026 : équipes et fiches, structures de service, cycle, moteur. Les 34 changes d'après ont été archivés le 23 septembre **sans** cette copie. Leurs exigences peuvent être dépassées.

Exemples dépassés dans ces quatre fichiers :

- Le bac à sable n'a plus une seule cible. Il y en a un par équipe.
- Le minimum de créneau est par service, pas un seul nombre par fiche.
- Le bien-être est une fiche structurée, pas un sac de drapeaux.
- Il n'y a plus de fichier `VERSION`. Banc et client ont chacun un choix en base.

Aucun change actif. Le choix de moteur est dans `archive/2026-09-24-bench-engine-choice/`.

On ne fusionne pas les 34 archives d'un coup. Quand un prochain change touche une de ces quatre specs, on la réécrit au présent à partir des contrats, puis on y pose le delta du nouveau besoin.
