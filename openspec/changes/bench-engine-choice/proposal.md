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
- Le moteur client (`live_engine_ref`) suit la même règle, avec sa propre valeur en base. Liste persistante. Rien de valable en base → dernier du registre, et on réécrit cette valeur.
- **BREAKING** : le fichier `data/bench/VERSION` disparaît. Sans choix valable, le banc et le generate restaurant passent de `core-5` au dernier du registre. `core-5` reste un moteur de la liste : c'est le code de `engine.py`, plus le défaut.

### Cas limites retenus

- Base vide → dernier du registre, puis ce nom est écrit.
- Nom stocké absent de la liste → même repli, et la base est réécrite.
- Un seul choix global. Le second admin qui choisit remplace le premier.
- L'enregistrement a lieu au choix dans la liste, pas au lancement.
- Échec d'enregistrement : la liste reste sur le choix précédent, le message d'erreur s'affiche.

### Hors-scope

- Fusionner les deux choix. Le banc et le restaurant gardent chacun le leur.
- Un moteur ajouté ensuite ne déplace pas un choix déjà enregistré. Seule une base vide ou un nom hors liste retombe sur le nouveau dernier.
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
- Un generate restaurant suit le choix client. Rien de valable en base → le dernier du registre, encore là après rechargement du sélecteur admin. Le choix du banc ne le change pas.
- Le fichier `data/bench/VERSION` n'existe plus. Aucun calcul ne le lit.
- Un nom invalide à l'enregistrement : 400, le choix précédent reste.

## Capabilities

### New Capabilities

- `bench-engine-choice`: le banc et le moteur client retiennent chacun un moteur choisi, et retombent sur le dernier du registre quand la base n'a pas de nom valable.

### Modified Capabilities

- Aucune. Les specs principales ne décrivent pas le banc.

## Impact

- Core : supprimer `data/bench/VERSION`. Un moteur omis au calcul domaine = le dernier du registre.
- Infra : Alembic `bench_engine` après `20260922_0019`. Le choix banc et le choix client (`live_engine`) utilisent le même repli. Plus aucune lecture du fichier.
- UI : listes du banc et du moteur client, rechargement, erreur si l'enregistrement échoue. Pas de `release.ts`.
- Contrat : `contracts/domain/bench-engine-choice.md` gagne sur `bench.md` et sur le repli de `admin.md`.
