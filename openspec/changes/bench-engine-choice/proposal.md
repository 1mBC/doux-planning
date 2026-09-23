# Proposal

## Why

Le sélecteur de moteur du banc repart sur le fichier `data/bench/VERSION` à chaque rechargement. L'opérateur a besoin que le moteur choisi reste, et que l'absence de choix valable prenne le dernier nom du registre du code.

## What Changes

- Un seul choix de moteur pour tout le banc, enregistré en base, partagé par tous les admins et par les deux pages (Banc IA, Banc Manuels).
- La liste affichée reste `list_engine_refs()`, dans l'ordre du registre. Un prochain change ajoute ou retire un moteur en modifiant ce registre. La liste n'est pas une table.
- Changer la liste déroulante enregistre tout de suite. Relancer une page relit ce choix.
- Aucune valeur en base, ou une valeur qui n'est plus dans la liste : le banc prend le dernier nom du registre (aujourd'hui `mix-0`) et réécrit la base avec ce nom.
- `GET /v1/admin/bench/versions` `engine_ref`, un `POST /v1/admin/bench/run` sans `engine_ref`, le compare-chemin et l'export `below_manuel` utilisent ce choix effectif.
- Un `POST` avec un `engine_ref` valide lance ce moteur pour cet appel seulement. Il ne change pas le choix enregistré.
- Un enregistrement invalide (vide, inconnu, mauvais type) répond 400 et laisse le choix précédent.
- **BREAKING** : sans choix valable, le banc ne lit plus `data/bench/VERSION`. Le défaut passe de `core-5` au dernier du registre.

### Cas limites retenus

- Base vide → dernier du registre, puis ce nom est écrit.
- Nom stocké absent de la liste → même repli, et la base est réécrite.
- Un seul choix global. Le second admin qui choisit remplace le premier.
- L'enregistrement a lieu au choix dans la liste, pas au lancement.
- Échec d'enregistrement : la liste reste sur le choix précédent, le message d'erreur s'affiche.

### Hors-scope

- Le sélecteur du restaurant (`live_engine_ref`) et son repli sur `VERSION`.
- Supprimer le fichier `data/bench/VERSION`.
- « Compléter les trous » : un job par moteur de la liste, sans utiliser le choix du banc.
- Le catalogue des 50 jeux, les formules de note, keep-best.
- Un choix par admin, ou une liste de moteurs saisie à la main.

### Critère de complet

- L'admin ouvre le Banc IA, choisit un moteur, recharge : le même moteur est encore sélectionné. Le Banc Manuels montre le même.
- Base vide : la liste affiche le dernier nom du registre, et un lancement sans moteur explicite utilise celui-là.
- Un nom stocké qui n'est plus dans la liste devient ce dernier nom, encore là après rechargement.
- Lancer tout, une catégorie, ou une ligne utilise le moteur choisi.
- Compléter les trous remplit encore chaque moteur de la liste.
- L'export sous le Manuel et le compare-chemin suivent le choix effectif.
- Un generate restaurant suit toujours `live_engine_ref`, et `VERSION` si rien de valable n'est stocké pour le restaurant.
- Un nom invalide à l'enregistrement : 400, le choix précédent reste.

## Capabilities

### New Capabilities

- `bench-engine-choice`: le banc retient un moteur choisi, et retombe sur le dernier du registre quand la base n'a pas de nom valable.

### Modified Capabilities

- Aucune. Les specs principales ne décrivent pas le banc.

## Impact

- Infra : Alembic après `20260922_0019`, lecture et écriture du choix, défaut des routes banc qui disaient « moteur courant = VERSION ».
- UI : liste déroulante des deux pages banc, rechargement, erreur si l'enregistrement échoue. Pas de `release.ts`.
- Core : le registre `list_engine_refs()` ne change pas. `engine_ref()` et le fichier `VERSION` restent le défaut du restaurant.
- Contrat : `contracts/domain/bench-engine-choice.md` gagne sur `bench.md` pour le moteur courant du banc.
