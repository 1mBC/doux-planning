# Bien-être, indispos, labels de semaine

Freeze **domaine** (moteur + fiches + hydrate).  
Tranche 15 : `weekend_rest_day`. Persist HTTP du bool = brief Infra. Wizard / types = brief UI.

Anciennes clés **supprimées** (pas d’alias) :  
`at_least_one_weekend_rest_day`, `no_evening_service`, `no_morning_service`,  
`max_two_coupures_per_week`, `max_three_coupures_per_week`.  
Plus de `every_morning` / `every_evening` sur une indispo.

## Wellbeing (une fiche)

Tout est du bien-être métier. Forme technique :

```
Wellbeing {
  consecutive_rest: bool                 # défaut false
  weekend_rest_day: bool                 # défaut false — au moins un repos sam ou dim, CHAQUE semaine
  weekend: null | "every_two" | "even" | "odd"
  max_services: { morning?: int, midday?: int, evening?: int }
  max_coupures_per_week: int | null      # défaut null
}
```

- `weekend_rest_day` : case **en plus** de la radio `weekend` (pas la même question : 1 jour we ≠ we complet).  
  Tenue **par** semaine du cycle : samedi **ou** dimanche sans shift. Jour resto **fermé** = repos (dimanche fermé → déjà tenu ; case quand même posable).
- `weekend` : **0 ou 1** choix (radio). `null` = pas de souhait we **complet**.  
  `every_two` = un week-end sur deux, **neutre** sur la parité.  
  `even` = week-end **paire** off. `odd` = week-end **impaire** off.
- `max_services.<id>` : entier ≥ 0. **Clé absente** = pas de plafond. **0** = zéro service de ce type.
- `max_coupures_per_week` : entier ≥ 0, **0 autorisé**. `null` = pas de plafond.

`Employee.max_evenings_per_week` / `max_mornings_per_week` **fusionnent** dans `max_services`. Plus de flags coupures dans un `frozenset` d’enum.

## Deux repos consécutifs **par** semaine

Pas « en semaine » (lun–ven seulement). Ven–sam, sam–dim, dim–lun **comptent**.

Un jour resto **fermé** (tous les services entreprise fermés ce weekday) **compte comme un repos**.

- 0 jour fermé → il faut une **paire** de repos adjacents dans la semaine (7 j.).
- 1 jour fermé → le 2ᵉ repos est **collé** à ce jour (dimanche fermé → samedi **ou** lundi).
- 2 jours fermés déjà collés → souhait tenu ; un 3ᵉ repos, s’il existe, **n’importe où**.
- 2 jours fermés **non** collés (ex. dimanche + mercredi) → les 2 repos « légaux » existent sans paire → tenu seulement si un **3ᵉ** repos vient se coller à l’un des deux.

Un 3ᵉ repos (au-delà de la paire) n’a pas de contrainte de place.

S’applique à **chaque** semaine du cycle (j0–6 et j7–13).

## Week-end (cycle 14 j.)

Semaine 1 du cycle = jours 0–6. Semaine 2 = jours 7–13.  
Le restaurateur aligne ça sur le calendrier réel **lui-même**. Pas de date ISO.

| `weekend` | Tenue |
|---|---|
| `every_two` | exactement **un** des deux week-ends (sam+dim) entièrement off |
| `even` | week-end **paire** (j5–6) off ; week-end impaire (j12–13) **pas** entièrement off |
| `odd` | week-end **impaire** (j12–13) off ; week-end paire **pas** entièrement off |
| `null` | pas de warning week-end |

## Labels de grille — **tout le resto**

```
week_label_scheme(state) -> "ab" | "parity"
```

- `"parity"` ssi **au moins une** fiche (salle **ou** cuisine) a `weekend` `even` ou `odd`.
- sinon `"ab"`.
- `every_two` seul → **`"ab"`**.

`"ab"` → libellés **A / B**. `"parity"` → **Paire / Impaire** (paire = j0–6, impaire = j7–13).  
Même lecture pour les deux équipes et pour le salarié.

## Indispos — produit jour × service

```
Unavailability { weekday, service_id }
```

Les deux champs **requis**. `weekday` ∈ `monday`…`sunday`. `service_id` ∈ services entreprise (`morning` / `midday` / `evening`).  
`blocks(weekday, service_id)` = égalité exacte. Plus de « journée entière » implicite : une journée = **un créneau par service ouvert** ce jour-là.

L’UI (plus tard) coche N jours × M services → N×M lignes. Synthèse FR = UI.

## Warnings moteur (`souhait`)

| Souhait | `code` |
|---|---|
| `consecutive_rest` | `consecutive_rest_days` |
| `weekend_rest_day` | `weekend_rest_day` |
| `weekend: every_two` | `weekend_every_two_weeks` |
| `weekend: even` | `weekend_even_weeks` |
| `weekend: odd` | `weekend_odd_weeks` |
| `max_services.morning` | `max_mornings` |
| `max_services.midday` | `max_middays` |
| `max_services.evening` | `max_evenings` |
| `max_coupures_per_week` | `max_coupures` |

Codes **retirés** : `no_evening`, `no_morning`. `weekend_rest_day` est **réintroduit** (bool objet, pas l’ancienne clé liste `at_least_one_weekend_rest_day`).

Le solveur doit **viser** ces souhaits (pas seulement les warning après coup). Formules légales inchangées.

## `employee_board` — `wishes`

Une entrée **par souhait posé** sur la fiche (pas les absents) :

```
{ "kind": "consecutive_rest", "held" }
{ "kind": "weekend_rest_day", "held" }
{ "kind": "weekend", "value": "every_two"|"even"|"odd", "held" }
{ "kind": "max_services", "service_id", "limit", "held" }
{ "kind": "max_coupures", "limit", "held" }
```

`held` = aucune warning `souhait` de ce `code` pour cet `employee_id` sur le result **publié**.

## Snapshot Saint-Cloud (`data/examples/saint-cloud.json`)

Adapter **sans** alias. Hydrate lit la **nouvelle** forme seulement.

| Avant | Après |
|---|---|
| `two_consecutive_rest_days` | `consecutive_rest: true` |
| `weekend_off_every_two_weeks` | `weekend: "every_two"` |
| `at_least_one_weekend_rest_day` | **supprimé** (pas de radio équivalente) |
| `max_two_coupures_per_week` | `max_coupures_per_week: 2` |
| `max_three_coupures_per_week` | `max_coupures_per_week: 3` |
| `max_evenings_per_week: 2` | `max_services.evening: 2` |
| `max_mornings_per_week: null` | clé absente |
| indispo `{ weekday, service_id: "midday" }` | inchangé (drop `every_*`) |
| indispo `{ weekday, service_id: null }` (journée) | une ligne **par** service ouvert du resto (Saint-Cloud : `midday` + `evening`) |

`forced_off_days` inchangé.

Si le solve (même effort que le snapshot, aujourd’hui `optimized`) **change** assignments / warnings / stats : **réécrire** le bloc `planning` du JSON. Remonter au facteur les **nouveaux** `stats.assignments` / `warnings.length` / `wellbeing.held` — **ne pas** éditer `contracts/http/v1-examples.md`. Si le solve est identique, ne pas toucher `planning`.

GET exemple public reste du **fichier** (pas un generate HTTP).

## Tests (cette tranche — `weekend_rest_day`)

- Dimanche **fermé** + `weekend_rest_day: true` → tenu **sans** autre repos we (le fermé compte).
- Dimanche **ouvert** + sam et dim travaillés → warning `weekend_rest_day`.
- Cumul `weekend_rest_day` + `weekend: even` (deux souhaits, deux codes).
- Clé absente → `false` : pas de warning, pas d’entrée board.
- Ancienne clé liste `at_least_one_weekend_rest_day` → **refusée** (pas d’alias).
- Saint-Cloud : **ne pas** réécrire `planning` (stats 92 / 17 / 10/12).
- Pytest domaine / engine / board / hydrate verts. Pas `api/`.

Régression wellbeing-model (déjà landed) : repos consécutifs, we even/odd/every_two, `max_services` / coupures 0, indispo jour×service.

## Hors freeze

Archive / sync. Wizard / types = `contracts/domain/wizard-ui.md`.
