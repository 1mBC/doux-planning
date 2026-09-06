# Sandbox live HTTP

Freeze HTTP. Wrappe `enter_live_sandbox` / `discard_live_sandbox` / `publish_live_sandbox` + preview/apply/undo Core (`contracts/domain/live-sandbox.md`).  
**Pas** les routes `/v1/sandbox/*` (joujou Saint-Cloud, public, inchangé).

Bearer **company**. `team` dans le path : `salle` | `cuisine`. Pas d’id resto (session).  
Employé → 403 `Action réservée au restaurateur.`  
Sans Bearer → 401 `Session invalide.`  
Sans `DATABASE_URL` → 503 `Base indisponible.`  
`NoPublishedCycle` → 409 `Aucun cycle publié pour cette équipe.`  
Team invalide → 400 `Champs invalides.`

Preview / commit / undo / history / score / impact / proposals = **mêmes shapes** que `contracts/http/v1-sandbox-edit.md`. Infra wrappe, ne rescore pas. Mêmes `detail` FR que le joujou (retune identité, case occupée, historique vide, etc.).

## Routes

```
POST /v1/live/sandbox/{team}/enter     → 200 LiveState
    body/query optionnel { "search_effort": "minimal"|"optimized"|"maximal" }
    défaut = latest ; slot vide → 409 `Aucun cycle publié pour cette équipe.`
GET  /v1/live/sandbox/{team}           → 200 LiveState  | 404 si pas de brouillon
POST /v1/live/sandbox/{team}/preview   → 200 { proposals }
POST /v1/live/sandbox/{team}/commit    → 200 LiveState
POST /v1/live/sandbox/{team}/undo      → 200 LiveState  | 409 si history vide
POST /v1/live/sandbox/{team}/discard   → 200 LiveState  (re-enter publié, history vide)
POST /v1/live/sandbox/{team}/publish   → 200 Cycles     (même `published` que GET /v1/cycles)
```

`LiveState` = état joujou (`sandbox`, `restaurant` fiches de **cette** équipe, `planning.assignments` + `warnings`, `score`, `history`) **plus** `"team": "salle"|"cuisine"`.

Discard : Core discard puis enter **le même** slot effort. Publish : réécrit `versions[effort]` (`generated_at` inchangé), `latest` inchangé sauf si ce slot est le seul, ferme le brouillon. `GET /v1/cycles` au format versions. L’autre équipe / les autres efforts intacts.

## Persist

Brouillons `live_sandboxes` sur l’entreprise live (pas `sandbox_sessions` Saint-Cloud, pas `example_snapshots`). Restart → même GET live. Joujou `/v1/sandbox/enter` sans Bearer toujours 200, exemple 92.

## UI (cette tranche)

`/planning` company : Mode édition → `/v1/live/sandbox/{team}/…` (Bearer). Même overlays que le joujou. Publier ferme le brouillon. `/exemple` continue d’appeler `/v1/sandbox/*` sans Bearer.

## Hors tranche

Jobs, semaines / reconciliation, `/me/shifts`, lock du joujou public.
