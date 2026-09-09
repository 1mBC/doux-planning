# Recaps d’un cycle publié (live)

Freeze **domaine**. HTTP persist = brief Infra. UI = brief UI.  
Facts / dictionnaire FR / clic notes = **`contracts/domain/score-facts.md` (gagne)**.  
Pas de second solve : lecture de `published_cycles[team].result` + fiches de l’équipe.

L’exemple public Saint-Cloud : rewrite = `contracts/domain/exemple-snapshot.md`.

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
    empty: int                         # evaluate empty_post
    interdit: int                      # evaluate severity interdit
    below_role: int
    hours: { assigned, contracted, percent }
    wellbeing: { held, total }
  }
  legal_cols: [{ id, label_fr }]
  legal_rows: [{ name, employee_id, cells: { rule_id: { ok, kind, payload } } }]
  wish_cols:  [{ key, label }]
  wish_rows:  [{ name, employee_id, cells: { key: { ok, kind, payload } | null } }]
  facts: ScoreFact[]                 # score-facts.md — miss evaluate puis hits
  score: CycleScore                  # score.md — plus de resumes
}
```

### `stats`

Inchangé vs tranche recaps :

- `assignments` = nombre de shifts du cycle.
- `empty` / `interdit` = comptes sur **evaluate** (miss `empty_post` / severity `interdit`).
- `below_role` = personne `level` > `post_level` du shift.
- `hours.assigned` / `contracted` / `percent` : 14 j., `round(100 * assigned / contracted)`.
- `wellbeing.total` / `held` : souhaits posés hors contrat.

### `legal_*`

Une ligne par fiche.  
`legal_cols` = règles `default_legal_rules` qui ont **au moins une** cellule.  
Salle : pas de colonne `max_daily_cuisine`. Cuisine : pas de `max_daily_salle`.

`ok` = aucune miss evaluate de ce kind pour cet `employee_id` (`rest_between_days` : aucune miss de ce kind).  
Cellule : `{ ok, kind, payload }` — payloads = `score-facts.md`. **Plus de `text`.**

`kind` moteur : `max_daily_hours` même si la **clé** de colonne est `max_daily_salle` / `_cuisine`.

### `wish_*`

Colonnes **nouveau** modèle — **pas** `we1j` / `weA` / …

| `key` | Label | Quand |
|---|---|---|
| `contrat` | Contrat | toujours |
| `indispo` | Indispos | si **au moins une** fiche a une indispo |
| `consecutive_rest` | Deux repos consécutifs par semaine | si posé sur ≥1 fiche |
| `weekend_rest_day` | Au moins un repos samedi ou dimanche | si posé |
| `weekend` | Week-end | si `weekend` non null sur ≥1 fiche |
| `max_morning` / `max_midday` / `max_evening` | Max petit-déj / déj / dîner | si `max_services.<id>` posé |
| `max_coupures` | Nbre de coupures max | si posé |

Cellule **null** = non émis pour cette fiche.  
`ok` = `held` du board (contrat / indispo : aucune miss de ce kind).  
`cell.kind` = kind moteur (`contract_hours`, `consecutive_rest_days`, `max_evenings`, …) — table `score-facts.md`.

## Evaluate (misses)

Toujours `evaluate`. `severity`, `code`/`kind`, `day_index` **inchangés** (cardinalité keep-best).  
À la place de `message` FR : `payload` (`score-facts.md`).  
`contract_hours` reste `souhait`.  
`empty_post` : `day_index` inchangé.  
`rest_between_days` : `day_index` = jour A ; payload avec les deux horloges (minutes).  
`weekend_every_two_weeks` peut rester sans `day_index`.

## UI (cette tranche + score-facts)

- Warning/fact `contract_hours` : pastille **Contrat**. Autres `souhait` : « Souhait ».
- Tableaux légal + souhaits : cellule `ok: false` → **orange + gras**. Titre wish : **Souhaits bien-être**.
- Liste alertes = facts miss hors `role_gap`, rendue par le dictionnaire.
- Clic notes = `score-facts.md`.
- `/planning` company : **Calculer** / **Mode édition** **sous** le switch Salle · Cuisine.

## Tests

- Resto salle généré `minimal` : une ligne légale par fiche ; pas de col `max_daily_cuisine`.
- Fiche avec `weekend_rest_day` : col présente.
- Paire < 11 h : fact `rest_between_days` avec `end_minutes` + `start_minutes_b` (pas de FR dans le payload).
- `empty_post` : `weekday` + `service_id` + horloges minutes + `post_level`.
- Wish `max_evening` : payload `limit` + `count_week_0` / `count_week_7`.
- Diane : cellule `contrat` `ok: false`, payload 30 / 29 / 39.
- Pas de `we1j` / `weA`. Pas de `message` / `text` / `resumes` sur un recap neuf.
- Hydrate / board / keep-best verts.

## Hors freeze

Keep-best. Panneau salarié FR. Archive / sync.
