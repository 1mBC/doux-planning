# Facts de score / feedback

Freeze **domaine**. HTTP = briefs Infra. Dictionnaire FR + clics = brief UI.  
**Coupe nette** : plus de `message` FR moteur, plus de `score.resumes` Core, plus de `text` FR dans les cellules recap. L’UI rend.  
Keep-best **inchangé** : `_attempt_key` / `SEARCH_*` / `generate_cycle` / `engine.py` ordre et comptes evaluate.

## Forme

```
ScoreFact {
  axis:      "couverture" | "legal" | "contrat" | "wellbeing" | "roles"
  kind:      string          # snake anglais, catalogue ci-dessous
  polarity:  "miss" | "hit"
  severity:  "interdit" | "couverture" | "souhait" | null
  employee_id: string | null
  day_index:   int | null
  payload:     object        # JSON, zéro FR, zéro nom de personne
}
```

- `kind` = l’ancien `code` evaluate (`empty_post`, `contract_hours`, …) **plus** `post_held` et `role_gap`.
- Miss evaluate : `severity` = celle d’aujourd’hui (`contract_hours` reste `souhait`). Hits : `severity` **null**.
- `payload` : minutes int, heures float, `weekday` anglais, `service_id`, `week_start` `0|7`, ids. **Pas** de `hours_label`, **pas** de jour FR, **pas** de sem. A/B.
- Noms : l’UI joint `employee_id` → fiche. Admin log peut ajouter `employee_name` (copie au moment du log).
- `key()` publish/ack : `(severity, kind, employee_id, day_index, payload canonique)`. Plus de `message`.

HTTP **n’émet plus** `warnings[]`, `code`, `message`. Clé unique : `facts[]`.

## Cycle (generate / cycles / hydrate / snapshot / export)

```
Cycle {
  assignments,
  facts,                 # miss d’abord (ordre evaluate), puis hits
  stats,                 # inchangé (empty / interdit / below_role / hours / wellbeing)
  legal_cols, legal_rows,
  wish_cols, wish_rows,
  score,                 # notes + weights + global — plus de resumes
  generated_at, search_effort, duration_seconds
}
```

`facts` **toujours** présent (tuple vide si rien). Ordre :

1. **Miss evaluate** — même cardinalité, mêmes `kind`/`employee_id`/`day_index` qu’aujourd’hui (`coverage` → `legal` → `unavailability` → `wellbeing` → `contract_hours`). Saint-Cloud : **17** misses evaluate.
2. **Miss `role_gap`** — un par assignment avec `gap > 0` (sous-rôle). **Pas** dans evaluate → keep-best inchangé.
3. **Hits** — `post_held` (scan couverture), puis cellules recap `ok`, puis `contract_hours` tenus (personne × semaine), puis `role_gap` `gap == 0`.

### Liste alertes (sous la grille)

Miss evaluate seulement : `polarity == "miss"` **et** `kind != "role_gap"`.  
Les sous-rôles se voient au clic de la pastille Rôles / Globale, pas dans la liste alertes.

### Clic pastille score (`/planning` + `/exemple`)

Une **seule** liste (overlay / panneau) :

1. misses de l’axe (`axis` de la pastille ; Globale = tous)
2. **juste en dessous**, tous les hits du même filtre

Enriched : titre dictionnaire + gabarit payload + nom + jour/semaine.  
Kind inconnu : afficher `kind` + payload brut, **ne pas inventer** de FR.

Résumé sous la pastille (plus `score.resumes`) : l’UI le compose (section Dictionnaire). `stats` + comptes de facts.

## Python Core

- `Warning.message` **supprimé**. `Warning.code` peut rester (= `kind`) + `payload: dict`.
- `evaluate()` : misses only, **mêmes comptes** qu’aujourd’hui. Payload à la place du FR.
- Hits : `cycle_recap` / helper `cycle_facts` — **pas** dans `EngineResult.warnings`.
- `CycleScore` : plus de `resumes` / `ScoreResumes`.
- `RecapCell` : `{ ok, kind, payload }` — plus de `text`.
- `refresh_example_snapshot` : réécrit `planning.facts` + cellules + `score` sans resumes. Assignments **92** inchangés.
- Employee board : `held` = aucune miss de ce `kind` pour l’id. Pas de FR ici.
- Sandbox `PreviewImpact` : les listes `new_interdits` / `broken_wishes` / `coverage_*` sont des `ScoreFact` (miss, payload, pas de `message`). `contract` / `role_fit` **inchangés** (déjà structurés).

## Hydrate (vieux JSONB)

GET ne sert **jamais** `message` / `resumes` / `text` comme source.  
Cycle sans `facts` : Core `cycle_recap` + evaluate sur assignments + fiches (comme resumes aujourd’hui).  
`generate_logs` anciens : item avec `message` et sans `payload` → Infra émet un fact `kind = code`, `polarity = miss`, `payload = {}`, **plus** `message` **uniquement** sur ces vieux rows (l’UI s’en sert en dernier recours). Écritures nouvelles : pas de `message`.

## Catalogue `kind`

| kind | axis | miss evaluate | hit |
|---|---|---|---|
| `empty_post` | couverture | slot requis vide | — |
| `post_held` | couverture | — | slot requis tenu (même boucle `derive_slices`) |
| `assigned_on_closure` | couverture | shift sur fermeture | — |
| `rest_between_days` | legal | paire < 11 h | cellule recap ok |
| `weekly_rest_days` | legal | semaine < 2 j. repos | cellule ok |
| `max_coupure` | legal | coupure > 5 h | cellule ok |
| `max_daily_hours` | legal | amplitude jour | cellule ok (`legal_cols` reste `max_daily_salle` / `_cuisine`) |
| `max_weekly_hours` | legal | > 48 h / sem. | cellule ok |
| `unavailability` | contrat | posé sur indispo | personne avec indispos, 0 miss |
| `contract_hours` | contrat | semaine hors tolérance | semaine dans tolérance (`C > 0`) |
| `consecutive_rest_days` | wellbeing | sem. sans 2 repos collés | cellule ok |
| `weekend_rest_day` | wellbeing | sem. sans repos sam/dim | cellule ok |
| `weekend_every_two_weeks` | wellbeing | pas un we / 14 j. | cellule ok |
| `weekend_even_weeks` | wellbeing | we pair non tenu | cellule ok |
| `weekend_odd_weeks` | wellbeing | we impair non tenu | cellule ok |
| `max_mornings` / `max_middays` / `max_evenings` | wellbeing | sem. au-dessus du max | cellule ok |
| `max_coupures` | wellbeing | sem. au-dessus du max | cellule ok |
| `role_gap` | roles | assignment `level - post_level > 0` | `gap == 0` |

Colonne recap `contrat` / `indispo` / `consecutive_rest` / `max_evening` : **clés de colonne inchangées**. `cell.kind` = kind moteur (`contract_hours`, `unavailability`, `consecutive_rest_days`, `max_evenings`, …).

## Payloads miss (evaluate)

Champs en plus de `employee_id` / `day_index` sur le fact. Omettre une clé absente plutôt que `null` décoratif.

**`empty_post`**

```
{ weekday, service_id, team, start_minutes, end_minutes, post_level }
```

**`assigned_on_closure`**

```
{ weekday, service_id }
```

**`max_daily_hours`**

```
{ hours, limit_hours }     # 11.5 salle / 11 cuisine
```

**`max_coupure`**

```
{ gap_minutes, limit_hours: 5 }
```

**`weekly_rest_days`**

```
{ rest_days, required: 2, week_start }
```

**`max_weekly_hours`**

```
{ hours, limit_hours: 48, week_start }
```

**`rest_between_days`** — `day_index` = jour A (dernier shift)

```
{ day_index_b, end_minutes, start_minutes_b, rest_minutes, required_minutes: 660 }
```

**`unavailability`**

```
{ weekday, service_id }
```

**`consecutive_rest_days` / `weekend_rest_day`**

```
{ week_start }
```

**`weekend_every_two_weeks` / `_even_weeks` / `_odd_weeks`**

```
{ off_week_0: bool, off_week_7: bool }
```

(`weekend_*` without `day_index` : inchangé.)

**`max_mornings` / `max_middays` / `max_evenings`**

```
{ count, limit, week_start, service_id, day_indexes: [int] }
```

**`max_coupures`**

```
{ count, limit, week_start }
```

**`contract_hours`**

```
{ hours, contracted, week_start }
```

**`role_gap`** (pas evaluate)

```
{ employee_level, post_level, gap, weekday, service_id, start_minutes, end_minutes, team }
```

`gap = employee.level - post_level`. Hit : `gap == 0`. Pas de fact si occupant inconnu.

**`post_held`** — même payload qu’`empty_post`.

## Payloads cellules recap (`{ ok, kind, payload }`)

Une cellule = agrégat d’affichage (souvent 14 j.). Facts score peuvent être plus fins (sem. / paire).

| col / rule | kind | payload |
|---|---|---|
| `rest_between_days` | `rest_between_days` | ok : `{ required_minutes: 660 }` ; miss : payload de la **première** paire cassée |
| `weekly_rest_days` | `weekly_rest_days` | `{ rest_days_week_0, rest_days_week_7, tightest, required: 2 }` |
| `max_coupure` | `max_coupure` | `{ max_gap_hours, limit_hours: 5 }` |
| `max_daily_salle` / `_cuisine` | `max_daily_hours` | `{ max_hours, limit_hours }` |
| `max_weekly_hours` | `max_weekly_hours` | `{ hours_week_0, hours_week_7, limit_hours: 48 }` |
| `contrat` | `contract_hours` | `{ hours_week_0, hours_week_7, contracted }` |
| `indispo` | `unavailability` | ok : `{ slot_count }` ; miss : `{ weekday, service_id }` du premier créneau cassé |
| `consecutive_rest` | `consecutive_rest_days` | ok : `{ left_weekday, right_weekday }` du premier pair collé si évident ; miss : `{ week_start }` de la première sem. cassée |
| `weekend_rest_day` | `weekend_rest_day` | ok : `{ off: "saturday"\|"sunday" }` ; miss : `{ week_start }` |
| `weekend` | `weekend_every_two_weeks` \| `weekend_even_weeks` \| `weekend_odd_weeks` | `{ weekend: "every_two"\|"even"\|"odd" }` |
| `max_morning` / `_midday` / `_evening` | `max_mornings` / `_middays` / `_evenings` | `{ limit, count_week_0, count_week_7, service_id }` |
| `max_coupures` | `max_coupures` | `{ limit, count_week_0, count_week_7 }` |

Diane Saint-Cloud `contrat` : `{ ok: false, kind: "contract_hours", payload: { hours_week_0: 30, hours_week_7: 29, contracted: 39 } }`.

Hits recap (facts polarité hit, cellules `ok`) : **même** `kind` + payload de la cellule ok.

## Dictionnaire UI (FR) — source de vérité affichage

Titres :

| kind | titre |
|---|---|
| `empty_post` | Poste vide |
| `post_held` | Poste tenu |
| `assigned_on_closure` | Shift sur fermeture |
| `rest_between_days` | Repos 11 h |
| `weekly_rest_days` | Repos hebdo |
| `max_coupure` | Coupure |
| `max_daily_hours` | Amplitude journalière |
| `max_weekly_hours` | Heures hebdo |
| `unavailability` | Indispo |
| `contract_hours` | Heures de contrat |
| `consecutive_rest_days` | Repos consécutifs |
| `weekend_rest_day` | Repos week-end |
| `weekend_every_two_weeks` | Un week-end / 14 j. |
| `weekend_even_weeks` | Week-end pair |
| `weekend_odd_weeks` | Week-end impair |
| `max_mornings` | Max petit-déj |
| `max_middays` | Max déjeuner |
| `max_evenings` | Max dîner |
| `max_coupures` | Max coupures |
| `role_gap` | Adéquation rôle |

Gabarit **liste** (miss / hit) — l’UI formate horloges (`23h` / `11h30`), jours FR, sem. A/B ou Paire/Impaire via `week_label_scheme` des fiches, `hours_label` côté client.

- `empty_post` / `post_held` : `{jour} · sem. {…} · {service FR} · {début}–{fin} · niveau {n}`
- `rest_between_days` miss : `{name} : moins de 11 h ({jourA} {fin} → {jourB} {début})` ; hit : `{name} : min 11 h`
- `contract_hours` : `{name} : {h} / {C} contrat (sem. {…})`
- `role_gap` miss : `{name} : niveau {L} sur poste {P}` ; hit : `{name} : niveau {P} exact`
- Autres : mêmes infos qu’aujourd’hui dans `cycle-recaps.md` warn-fr, interpolées depuis le payload.

Gabarit **cellule** recap : mêmes mesures qu’aujourd’hui (`OK ·` si `ok`, `30h · 29h / 39h` pour contrat, `max {limit} · {nA} / {nB} posés`, etc.) — **composés dans l’UI**, plus dans Core.

Pastille alerte : `contract_hours` → **Contrat** ; autres `souhait` → Souhait ; `interdit` / `couverture` inchangés.

### Résumés sous pastille (ex-`resumes`)

L’UI, pas Core :

- couverture : `{post_held} / {post_held + empty_post} postes tenus` (équivalent `stats`)
- legal : `{cellules ok} / {cellules}` — compter les cells recap, **pas** les paires evaluate
- occupation : `{stats.hours.assigned occupées} / {contracted contrat}` puis ligne `{ok}/{n} indispos tenues` si col indispo
- wellbeing : `{stats.wellbeing.held} / {total} souhaits tenus`
- rôles : `{N} affectés · {k} poste en sous-rôle / {N}` (`stats.assignments` / `below_role`)

## Surfaces (toutes adaptées, pas de dual-write)

| Surface | Avant | Après |
|---|---|---|
| POST generate / job / GET cycles | `warnings[].message`, `score.resumes`, cells `text` | `facts[]`, `score` sans resumes, cells `kind`+`payload` |
| GET `/v1/examples/saint-cloud` | `planning.warnings` 17 messages | `planning.facts` (17 misses evaluate + hits) |
| Export JSON planning | `warnings` tel quel | `facts` |
| Admin `generate_logs` hover | `message` + `employee_name` | facts + `employee_name` ; vieux rows : fallback `message` |
| Banc `bench_runs.warnings` | serialize Warning+message | facts misses evaluate (payload) ; compare UI dictionnaire |
| Sandbox overlay `impact.*` | `warning.message` | facts ; `contract` / `role_fit` inchangés |
| Live sandbox `planning` | warnings | même Cycle `facts` |
| Employee board | codes warning | miss `kind` (déjà) — **pas** de rewrite des textes panneau |

## Tests (ancre)

- Saint-Cloud : 92 shifts ; Théo 11h–16h ; Diane contrat payload `30` / `29` / `39`, `ok: false` ; **17** facts miss evaluate (`kind != role_gap`) ; 0 `we1j` ; `stats` inchangés (0 empty, 0 interdit, 47 below_role, wellbeing 10/12).
- Aucun `message` / `resumes` / `cell.text` sur un cycle **nouveau**.
- `_attempt_key` / generate déterministe **inchangés**.
- `publish_allowed` : `key()` sans message, avec payload.
- Pytest engine / recap / board / hydrate / preview sandbox verts.

## Hors freeze

Keep-best. Poids éditables. Textes panneau salarié (`rest_day_label`, etc.). Archive / sync.
