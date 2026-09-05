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

Colonne **à part** de la radio week-end : **« Au moins un repos samedi ou dimanche »**.  
Sous-texte possible : chaque semaine ; un jour resto fermé compte.  
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
Pickers sur **l’échelle de l’équipe** (niveaux), **pas** de saisie `;` / virgules.

**Ligne arrivée** : heure (±15) + N personnes + **exactement N** niveaux min (un picker par personne).  
Afficher le **sac courant** après cette ligne.

**Ligne départ** : heure (±15) + K qui partent + **reste obligatoire par niveau** (entier ≥ 0 ; **0** = pas de contrainte sur ce niveau).  
L’UI calcule `remaining_post_levels` ; l’utilisateur ne l’édite pas à la main.

Plusieurs lignes arrivée / départ par type. Pouvoir ajouter / retirer.

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

## Hors freeze

Generate, formules moteur, coerce Railway, archive / sync.
