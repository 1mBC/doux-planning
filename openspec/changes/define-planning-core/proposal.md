## Why

Un restaurateur à taille humaine n’a pas d’outil pour poser un planning de croisière stable (cycle de 14 jours), l’adapter à la volée, et voir clairement ce qui casse (légal, couverture, bien-être). Sans modèle partagé dès le départ — postes, cycle vs instance, bac à sable, moteur unique — on construit un calendrier au lieu d’un moteur de contraintes.

## What Changes

- Introduire le modèle métier : équipes (salle / cuisine), rôles à niveaux, employés (contrat, indisponibilités, préférences de bien-être), structures de service par vagues, règles légales affichées.
- Introduire le planning de croisière : cycle répétable de 14 jours, instances calendaires, exceptions stockées comme intents (pas seulement une grille).
- Introduire un bac à sable à une cible (cycle **ou** une semaine), pour enchaîner des modifications (y compris config structurelle) avant publication.
- Introduire un moteur unique : générer, scorer / warner, classer des candidats (ajout, échange), affectation par postes avec descente au plus proche.
- La génération ne dépasse pas le contrat d’un employé tant que des collègues ont encore des heures à faire. Les jours de repos ne doivent pas s’empiler au point de laisser des postes vides alors que du monde est sous-heures. Un passage glouton qui laisse un trou est relancé (plusieurs départs déterministes) jusqu’à un meilleur arrangement.
- Application web desktop responsive. Pas d’app stores. Un restaurant, un restaurateur pour ce premier jet.
- Stack : Python 3.12 + FastAPI + OR-Tools, PostgreSQL, React + TypeScript, Docker Compose. L’API est le contrat pour le web et une app mobile plus tard. Notifications, contraintes saisies par l’employé, remplissage des extras : hors scope.

## Capabilities

### New Capabilities

- `staff-configuration`: équipes, rôles et niveaux, employés, contrat, indisponibilités, bien-être, code d’invitation.
- `service-structures`: mode continu ou par services, fermetures, vagues d’arrivée/départ, jours d’application, pas de 15 min.
- `cruise-planning`: cycle 14 jours, instances, intents, bac à sable à une cible, publication, réconciliation des semaines sales.
- `constraint-engine`: génération, évaluation, suggestions, warnings à trois gravités, règles légales, matching de postes.

### Modified Capabilities

- (aucune — projet vide)

## Impact

Aucun code applicatif encore. Ce change pose le contrat comportemental et la stack. L’implémentation commence par le module Python (domaine + moteur + bac à sable) ; le client React suit dans un change dédié.
