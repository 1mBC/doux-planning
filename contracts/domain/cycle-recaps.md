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
`ok` = `held` du board (contrat / indispo : aucune warning de ce code).

Textes **comme le légal** : toujours une **mesure**, pas seulement OK / Non tenu.

| `key` | Texte |
|---|---|
| `contrat` | inchangé `{hA}h · {hB}h / {weekly}h` |
| `indispo` | `OK · {n} créneaux` / `Non tenu · {jour} {service}` (le premier cassé) |
| `consecutive_rest` | `OK · tenu` + jours si évidents / `Non tenu · sem. A` (semaine du warning) |
| `weekend_rest_day` | `OK · sam` ou `OK · dim` (jour off tenu) / `Non tenu · sem. A` |
| `weekend` | `OK · {valeur FR}` / `Non tenu · {valeur FR}` |
| `max_morning` / `_midday` / `_evening` | souhait **d’abord** : `max {limit} · {nA} / {nB} posés` ; préfixe `OK · ` si tenu. Ex. fail : `max 2 · 1 / 3 posés` |
| `max_coupures` | même schéma `max {limit} · {cA} / {cB}` |

`nA` / `nB` = compte de ce service (ou coupures) semaine 1 / 2.

## Warning `rest_between_days`

Enrichir **`evaluate`** (donc tout live / sandbox qui ré-évalue). `day_index` reste le jour **A** (dernier shift).  
`message` FR, **deux horloges** :

```
{name} : moins de 11 h de repos ({jourA} {fin} → {jourB} {début})
```

Jours FR (`lundi`…`dimanche`). Heures `23h` / `11h30` (comme `formatClock`).  
Ne pas chasser un faux positif 11 h.

## Warnings `empty_post` / max services (cette tranche)

Toujours `evaluate`. `severity` **inchangée** (`couverture` / `souhait`). `contract_hours` reste `souhait` (le label « Contrat » = UI).

**`empty_post`** — `day_index` inchangé. Message FR :

```
{jour} · sem. {A|B|Paire|Impaire} · {service FR} · {début}–{fin} · niveau {n}
```

Semaine = `week_label_scheme` des fiches du draft (`even`/`odd` → Paire/Impaire, sinon A/B). Jour 0–6 = A/Paire, 7–13 = B/Impaire. Services : petit-déjeuner / déjeuner / dîner. Horloges `format_clock`.

**`max_mornings` / `max_middays` / `max_evenings`** — `day_index` = début de semaine. Message FR :

```
{name} : {n} {service FR} / max {limit} ({jours} · sem. {…})
```

`jours` = jours FR de **cette** semaine où la personne a ce service.  
`max_coupures` : `{name} : {n} coupures / max {limit} (sem. {…})`.

Ne pas traduire les **autres** codes (contrat anglais OK). **Ne pas** réécrire `saint-cloud.json`.

## Tests

- Resto salle généré `minimal` : `cycle_recap` a une ligne légale par fiche ; pas de col `max_daily_cuisine` ; `stats.assignments` = `len(assignments)`.
- Fiche avec `weekend_rest_day` : col présente ; fiche sans → cellule `null` si la col existe via un collègue.
- Paire de shifts qui casse 11 h : warning `rest_between_days` contient les deux horloges + jours FR.
- `empty_post` : jour FR + sem. + service + horloges.
- `max_evenings` : jours de la semaine + `max {limit}` dans le message.
- Wish `max_evening` : texte `max {limit} · {nA} / {nB} posés`.
- Pas de `we1j` / `weA`. Hydrate / board / exemple public verts. **Ne pas** réécrire `saint-cloud.json`.

## Hors freeze

Label UI « Contrat », cases orange, invite / QR, style types, exports, admin, archive / sync.
