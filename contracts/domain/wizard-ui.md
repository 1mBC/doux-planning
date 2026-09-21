# Wizard `/context` + Services types

Freeze **UI**. HTTP / moteur inchangés. Persist `types[]` = `contracts/http/v1-context.md`.

## Ordre des onglets

**Services → Rôles → Équipe → Souhaits bien-être → Services types → Semaine type.**

- **Services** : une fois, tout le resto (petit-déj / déj / dîner). Si la liste est vide, on reste ici.

**Ordre d’affichage** des services **partout** (Services types, semaine type, souhaits, planning) : `morning` → `midday` → `evening` (petit-déj, déj, dîner). **Pas** l’ordre des clics / du tableau `services` persisté. Implémentation : `CONTEXT_SERVICES.filter(s => offered.includes(s.id))` — jamais `services.map` pour des onglets / colonnes. Pas de `continuous` / `chambres` (hors freeze).
- Rôles / Équipe / Souhaits / Services types / Semaine type : **par équipe** (salle / cuisine), comme aujourd’hui.
- Souhaits **n’est pas** un cran de `ready` : on peut les laisser vides et continuer.
- Déblocage : services choisis → rôles ; échelle → équipe ; ≥1 fiche → souhaits **et** types ; types de l’équipe → semaine type.

## Décocher un service

Avant d’enregistrer : **warning FR** (une phrase : ça efface types, cases de semaine, indispos et plafonds de ce service).  
Si confirmé, **supprimer** (pas d’orphelin) :

- `types[]` avec ce `service_id` (**les deux** équipes) ;
- cellules `typical_week` des deux équipes pour ce `service_id` ;
- `unavailabilities[]` avec ce `service_id` (toutes fiches) ;
- `max_services.<id>` sur toutes les fiches.

PATCH d’un coup : `services` + `employees` + `types` + `typical_week` **nettoyés** (listes complètes, garder l’autre équipe).

Service **non offert** : **invisible** partout (max souhaits, popup indispo, Services types, semaine type). Plus de fallback « les 3 » si `services` est vide.

## Case `weekend_rest_day`

Colonne **à part** de la radio week-end : un `<th>` **« Au moins un repos samedi ou dimanche »**, case **dans cette colonne seulement** (plus dans la cellule Week-end).  
**Pas** de sous-texte par ligne.  
JSON `wellbeing.weekend_rest_day` bool. **Cumulable** avec `weekend`.  
GET `/v1/me/planning` : `kind: "weekend_rest_day"` → **même** libellé, tenu / non tenu.

Types TS : le bool est **requis** (Infra l’expose toujours). Ancienne clé liste → throw.

## Services types

Onglet libellé **Services types** (plus « Types »).  
Sous-onglets = services **offerts** seulement (**pas** de phrase UI « Sous-onglets = services offerts »).  
**Ajouter un type** en bas du sous-onglet courant (équipe × ce service). Plusieurs types par service OK.

### Vagues — l’UI calcule, le moteur ne change pas

Persister uniquement la forme actuelle :

```
arrivals[]:    { time_minutes, post_levels }            # length === N arrivants
departures[]:  { time_minutes, remaining_post_levels }  # sac APRÈS le départ
```

Pas de joker moteur. Pas de champ « qui part » persisté.

**Dessin** : **une `<table>` par feuille** (nom du type). Lignes chrono (arrivées + départs). Plus de cartes `wave-line`.  
Ajouter = arrivée **ou** départ. Retirer = poubelle. Persist / pire-cas inchangés.

Colonnes (thead une fois, libellés **fixes**) :

| Type | Heure | Niveaux minimal requis (par arrivée \| après départ) | STAFF minimal resultant |
|---|---|---|---|
| **Arrivée** ou **Départ** | cadran (voir plus bas) + ±15 | chaque niveau + stepper | sac / erreur |

**Pas** de colonne N / K. Arrivée : `post_levels` = concat des compteurs (somme = N, **invisible**). Départ : K = (taille du sac avant) − somme(à garder) ; `remaining_post_levels` = sac après pire-cas, comme aujourd’hui.

Libellé **Départ** (plus « Sortie ») **uniquement** dans cette table (cellule Type + thead). JSON / types TS : `departures` inchangé. Bouton déjà « Ajouter un départ ».

Plusieurs lignes. Ordre d’affichage = ordre d’application.

**Ordre d’application** : toutes les lignes (arrivées + départs) par `time_minutes` croissant ; à égalité, arrivées **avant** départs.

### Cadran d’heure (arrivée / départ)

Pas de `prompt()`. Dialog (même chrome `overlay-backdrop` + `overlay` que l’invite) :

1. **Ajouter une arrivée / un départ** → ouvrir le cadran **avant** d’insérer la ligne. Prérempli 11h00 / 16h00. Annuler / Escape / clic backdrop = **pas** de ligne.
2. Clic sur l’heure affichée du stepper → même cadran, valeur courante. Annuler = inchangé.

Deux cadrans côte à côte :

- **Heure** : boutons `0`…`23` **ou** saisie manuelle (entier 0–23).
- **Minutes** : boutons `00` / `15` / `30` / `45` **ou** saisie manuelle (entier 0–59).

Valider désactivé si invalide. Persisté : `time_minutes = hour * 60 + minutes` (0…1439). Si la ligne éditée avait déjà `time_minutes >= 1440` (fin de service / lendemain, le moteur s’en sert), **garder** `floor(old / 1440) * 1440` et y ajouter le cadran — ne pas ramener minuit-fin à 00h du matin. `formatClock` wrappe déjà l’affichage ; ne pas y toucher.

Stepper ±15 **reste** (niveaux + heure). Pas de plafond (on peut toujours dépasser 24h au stepper).

### Réordonnancement doux

Quand une heure change (± **ou** cadran) et que l’ordre chrono des lignes bouge : animer le déplacement **≥ 500 ms**, visible (pas un snap). Ligne éditée : fond focus **tant qu’une autre heure n’est pas éditée**. `prefers-reduced-motion` : snap OK, focus quand même. Clés React stables (`a-${index}` / `d-${index}` du draft, pas la position triée). ± des **niveaux** : pas d’anim. Pas de nouvelle dépendance npm.

**Pire cas (qui part)** — sac = multiset de niveaux présents juste avant ce départ :

1. Réserver, pour chaque niveau L avec reste obligatoire N_L > 0, **exactement** `min(N_L, count(L))` personnes de niveau L.
2. Parmi **tous les autres** (plus haut, plus bas, ou surplus du même niveau), retirer les **K plus hauts** niveaux.
3. `remaining_post_levels` = sac restant, **tri croissant**. C’est ce qu’on PATCH.

Exemples (K = 1) :

| Sac avant | Reste obligatoire | Part | Sac après |
|---|---|---|---|
| 1,2,3,4 | un 3 | 4 | 1,2,3 |
| 1,2,2,3 | un 3 | un 2 | 1,2,3 |
| 1,2,3,3 | un 3 | un 3 (surplus) | 1,2,3 |
| 1,2,2,3 | un 2 | 3 | 1,2,2 |
| 1,2,2,3 | un 3 et un 2 | un 2 (surplus) | 1,2,3 |

K > nombre de personnes non réservées → bloquer l’enregistrement (phrase FR).  
N_L > `count(L)` dans le sac → bloquer.

## Stepper (chrome)

Snippet **encadré** : libellé **gras** + `[−]` + compteur **centré** + `[+]`.  
Même composant : rôles, types (niveaux), overlay sandbox, ±15.

## Rôles

`<table>` **Rôle** / **Niveau de compétence** (stepper) / poubelle. Pas de nouvelle clé persistée.  
Sous-titre : **« Un niveau plus élevé est capable de tenir un poste de niveau inférieur. »** (plus « peut tenir un poste inférieur »).

Supprimer un rôle → **confirm FR** : lister les **fiches** qui ont ce rôle, dire qu’il faudra les revoir / recalculer, **conseiller de renommer** plutôt que supprimer. Si confirmé : retire la ligne (fiches inchangées jusqu’au save).

## Grille planning (company / exemple / salarié)

Cellules **H** (durée du shift, 3ᵉ colonne par jour) : même `--ink` que la personne, **plus pâle** que Début / Fin (`td.work`). Total heures **semaine** à droite : inchangé.

## Copies à retirer (cette tranche)

- **Équipe** : plus de phrase sous le titre ; plus de ligne texte d’indispos (chips seuls).
- **Souhaits** : plus de phrase sous le titre.
- **Semaine type** : plus « Libellés de cycle… » ni « L’autre équipe est renvoyée… ».

## Invite employés

Plus de **jeton** / **URL** sous chaque fiche.  
À côté du code entreprise : bouton **« Inviter mes employés »** → popup : **afficher + copier** le `company_code` **et** l’URL **absolue** `origin + /register?company_code={code}` (même valeur que le QR). Path seul (`/register?…`) **interdit** au presse-papiers (inutile sur téléphone).  
Les `invite_token` restent dans l’API / les fiches — **masqués** seulement. Pas de nouvelle route, pas de rotate.

## Hors freeze

Supprimer un salarié / unlink / panneau compte (**annulé**). Archive / sync.  
`continuous` / chambres (moteur pas prêt).
