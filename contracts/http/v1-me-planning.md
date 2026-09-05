# Planning salarié

Freeze HTTP. Wrappe `employee_board` (`contracts/domain/employee-board.md`).  
Bearer **employee** (`me.employee_id`). Pas d’id resto / fiche dans le path.  
`kind: company` → 403 `Action réservée au salarié.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`

Pas `/v1/me/shifts`. Pas de brouillon live. Pas de `invite_token`. Pas de `legal_rows` / `wish_rows` snapshot.

## Route

```
GET /v1/me/planning   Bearer employee → 200 EmployeePlanning
```

```
{
  "employee_id": "...",
  "team": "salle"|"cuisine",
  "week_labels": "ab"|"parity",
  "employees": [{ "id", "name", "role": { "name", "level", "team" }, "team" }],
  "assignments": [ Shift ],
  "contract": { "weekly": number, "assigned": number, "ok": bool },
  "wishes": [ /* forme wellbeing.md : kind consecutive_rest | weekend_rest_day | weekend | max_services | max_coupures */ ],
  "unavailabilities": [{ "weekday", "service_id" }]
}
```

`Shift` = mêmes clés que `GET /v1/cycles`.  
`employees` = fiches **de son équipe** (noms pour la grille).  
`assignments` = **toute** l’équipe publiée (`employee_board`) ; vide si pas de cycle.  
`wishes` / `contract` / `unavailabilities` = Core, lecture seule.

## UI (cette tranche)

`kind: employee` → `/planning` + `GET /v1/me/planning`. Grille équipe, lignes du salarié colorées, panneau contrat / indispos / souhaits lecture. Pas de Calculer ni Mode édition.

## Hors tranche

Edit salarié, generate, live sandbox, joujou.
