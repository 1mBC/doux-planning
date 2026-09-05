# Recaps d’un cycle publié (live)

Freeze **domaine**. HTTP persist = brief Infra. UI pastilles / tableaux / types = brief UI.  
Pas de second solve : lecture de `published_cycles[team].result` + fiches de l’équipe.

L’exemple public Saint-Cloud (`data/examples/saint-cloud.json`) **reste le snapshot figé**. Ne pas le réécrire. Ses `wish_cols` (`we1j`, `weA`…) sont **mortes** pour le live.

## API

```
NoPublishedCycle
cycle_recap(state, team) -> CycleRecap
```

Pas de cycle → `NoPublishedCycle`. Pas d’appel `generate_cycle`.

```
CycleRecap {
  stats: {
    assignments: int
    empty: int                         # warnings code empty_post
    interdit: int                      # severity interdit
    below_role: int                    # même compteur que _below_role_count
    hours: { assigned, contracted, percent }
    wellbeing: { held, total }
  }
  legal_cols: [{ id, label_fr }]
  legal_rows: [{ name, employee_id, cells: { rule_id: { ok, text } } }]
  wish_cols:  [{ key, label }]
  wish_rows:  [{ name, employee_id, cells: { key: { ok, text } | null } }]
}
```

### `stats`

- `assignments` = nombre de shifts du cycle.
- `empty` / `interdit` = comptes sur `result.warnings`.
- `below_role` = personne `level` > `post_level` du shift (helper moteur, pas une 2ᵉ formule).
- `hours.assigned` = somme `duration_hours` du cycle (14 j.).
- `hours.contracted` = somme `contractual_hours_per_week` × **2** (les deux semaines).
- `hours.percent` = `round(100 * assigned / contracted)` (0 si contracted = 0).
- `wellbeing.total` = souhaits **posés** (même règle que `employee_board.wishes`, **pas** le contrat).
- `wellbeing.held` = ceux avec `held` vrai. Contrat **hors** ce compteur.

### `legal_*`

Une ligne par fiche de l’équipe.  
`legal_cols` = règles `default_legal_rules` qui ont **au moins une** cellule.  
Salle : pas de colonne `max_daily_cuisine`. Cuisine : pas de `max_daily_salle`.

Textes FR (affichés tels quels) :

| `id` | OK | Non OK |
|---|---|---|
| `rest_between_days` | `OK · min 11h` | mêmes horloges que le warning enrichi |
| `weekly_rest_days` | `OK · N / 2 j.` (N = repos de la semaine la plus juste) | `N / 2 j.` |
| `max_coupure` | `OK · max {durée}` | `max {durée}` |
| `max_daily_salle` / `_cuisine` | `OK · max {durée}` | `max {durée}` |
| `max_weekly_hours` | `OK · {sem1}h / {sem2}h` | idem sans `OK ·` |

`ok` = aucune warning `interdit` de ce code pour cet `employee_id`.  
`rest_between_days` : `ok` ssi aucune warning de ce code pour la personne.

### `wish_*`

Colonnes **nouveau** modèle — **pas** `we1j` / `weA` / `weB` / `soirs` / `repos2`.

| `key` | Label | Quand |
|---|---|---|
| `contrat` | Contrat | toujours |
| `indispo` | Indispos | si **au moins une** fiche de l’équipe a une indispo |
| `consecutive_rest` | Deux repos consécutifs par semaine | si posé sur ≥1 fiche |
| `weekend_rest_day` | Au moins un repos samedi ou dimanche | si posé |
| `weekend` | Week-end | si `weekend` non null sur ≥1 fiche |
| `max_morning` / `max_midday` / `max_evening` | Max petit-déj / déj / dîner | si `max_services.<id>` posé |
| `max_coupures` | Nbre de coupures max | si posé |

Cellule **null** = non émis pour cette fiche.  
`ok` / `text` : contrat = `{hA}h · {hB}h / {weekly}h` (`ok` = aucune warning `contract_hours`) ; indispo = `ok` ssi aucune warning `unavailability` ; souhaits = `held` du board (`OK` / `Non tenu`, weekend : ajouter la valeur FR).

## Warning `rest_between_days`

Enrichir **`evaluate`** (donc tout live / sandbox qui ré-évalue). `day_index` reste le jour **A** (dernier shift).  
`message` FR, **deux horloges** :

```
{name} : moins de 11 h de repos ({jourA} {fin} → {jourB} {début})
```

Jours FR (`lundi`…`dimanche`). Heures `23h` / `11h30` (comme `formatClock`).  
Ne pas traduire les **autres** messages dans cette tranche.  
Ne pas chasser un faux positif 11 h.

## Tests

- Resto salle généré `minimal` : `cycle_recap` a une ligne légale par fiche ; pas de col `max_daily_cuisine` ; `stats.assignments` = `len(assignments)`.
- Fiche avec `weekend_rest_day` : col présente ; fiche sans → cellule `null` si la col existe via un collègue.
- Paire de shifts qui casse 11 h : warning `rest_between_days` contient les deux horloges + jours FR.
- Pas de `we1j` / `weA` dans `wish_cols`.
- Hydrate / exemple public / board : verts. **Ne pas** réécrire `saint-cloud.json`.

## Hors freeze

Pastilles UI, dessin Services types, archive / sync. HTTP persist = brief Infra.
