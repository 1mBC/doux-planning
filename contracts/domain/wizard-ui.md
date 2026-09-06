# Wizard `/context` + Services types

Freeze **UI**. HTTP / moteur inchangés. Persist `types[]` = `contracts/http/v1-context.md`.

## Ordre des onglets

**Services → Rôles → Équipe → Souhaits bien-être → Services types → Semaine type.**

- **Services** : une fois, tout le resto (petit-déj / déj / dîner). Si la liste est vide, on reste ici.
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
Sous-onglets = services **offerts** seulement.  
**Ajouter un type** en bas du sous-onglet courant (équipe × ce service). Plusieurs types par service OK.

### Vagues — l’UI calcule, le moteur ne change pas

Persister uniquement la forme actuelle :

```
arrivals[]:    { time_minutes, post_levels }            # length === N arrivants
departures[]:  { time_minutes, remaining_post_levels }  # sac APRÈS le départ
```

Pas de joker moteur. Pas de champ « qui part » persisté.

**Dessin (brief UI polish)** : **une liste chronologique** (arrivées et départs mélangés). Chaque événement = **une carte / ligne** (`wave-line` / `fiche-card`), **pas** un `<table>` tableur (plus de `wave-table` 5 colonnes + thead interminable).  
Ajouter = choisir arrivée **ou** départ. Retirer = poubelle en bout de ligne.  
Libellés courts **une fois** au-dessus de la liste (Heure · N · Niveaux · STAFF après). Persist / pire-cas inchangés.

Colonnes :

| | Arrivée | Départ |
|---|---|---|
| Heure | horloge **et** ±15 **sur la même ligne** | idem |
| Nombre | N arrivants — compteur lisible (pas un stepper nu) | N partants (K) — même compteur |
| Niveaux | **chaque** niveau de l’échelle + compteur **+/−** = combien à ce min | **chaque** niveau + compteur **+/−** = combien **à garder** (0 = pas de contrainte) |
| Dernière | en-tête **STAFF après cette arrivée / ce départ** (une fois). Cellule = sac / erreur, **sans** répéter « STAFF après : » | idem |

`post_levels` persisté = le multiset « N × niveau » des compteurs arrivée (somme = N).  
L’UI calcule `remaining_post_levels` ; l’utilisateur ne l’édite pas.

Plusieurs lignes. Ordre d’affichage = ordre d’application.

**Ordre d’application** : toutes les lignes (arrivées + départs) par `time_minutes` croissant ; à égalité, arrivées **avant** départs.

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

## Rôles (style)

Même langage visuel que l’équipe (ligne **Nom** + **Niveau**). Niveau en stepper **+/−**, pas un number input nu. Pas de nouvelle clé persistée.

## Invite employés

Plus de **jeton** / **URL** sous chaque fiche.  
À côté du code entreprise : bouton **« Inviter mes employés »** → popup : **afficher et copier** l’URL **absolue** `origin + /register?company_code={code}` (même valeur que le QR). Path seul (`/register?…`) **interdit** au presse-papiers (inutile sur téléphone).  
Les `invite_token` restent dans l’API / les fiches — **masqués** seulement. Pas de nouvelle route, pas de rotate.

## Hors freeze

Export config, exports planning, admin, coerce Railway, archive / sync.
