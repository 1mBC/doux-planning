# Contrats d’interface

Propriétaire : **orchestrateur** (chat Tech Lead).  
Core, UI et Infra **lisent** ces fichiers. Ils ne les modifient pas. Un champ manquant = stop, remonter au facteur, ne pas inventer.

OpenSpec (`openspec/changes/…`) décrit le comportement métier.  
Ce dossier fige les **shapes HTTP** (routes, clés JSON, invariants). En cas de conflit de forme, ce dossier gagne.

## Tranches

| Tranche | Fichier | Consommateurs |
|---|---|---|
| 0 — exemple public | `http/v1-examples.md` | UI + Infra |
| 1 — auth | `http/v1-auth.md` ; brief `ui-auth-screens.md` | UI (Infra HTTP fait) |
| 2 — édition sandbox | `http/v1-sandbox-edit.md` | Infra + UI (HTTP actuel) |
| 3 — feedback overlay | `http/v1-sandbox-edit.md` | fusionné dans `preview-sandbox-edits` |
| 4 — rôle / downrole | `http/v1-sandbox-edit.md` (`impact.role_fit`) | swap = créneau cliqué (pas la somme des deux) |
| 5 — case vide | `http/v1-sandbox-edit.md` (`gesture: fill`) | fait |
| 6 — fin sandbox | `http/v1-sandbox-edit.md` (`discard` + recap `history`) | fait |
| 7 — auth / QR | `http/v1-auth.md` | close (signaux Core → Infra → UI) |
| 8 — contexte onboarding | `http/v1-context.md` | close (signaux Core → Infra → UI) |
| 9 — generate / cycles | `http/v1-generate.md` | close (signaux Core → Infra → UI) |
| 10 — sandbox live | `http/v1-live-sandbox.md` | close (signaux Core → Infra → UI) |
| 11 — grille employé | `http/v1-me-planning.md` | close (signaux Core → Infra → UI) |
| 12 — recette Railway | `deploy/railway.md` ; brief `infra-deploy-railway.md` | Infra (auto-deploy `master`) |
| 13 — bien-être / indispos | `domain/wellbeing.md` | **landed** `11dc586` |
| 14 — seed exemple | `domain/example-seed.md` | **landed** `295bc9f` |
| 15 — repos we + wizard | `domain/wellbeing.md`, `domain/wizard-ui.md` | **landed** `6c75004` |
| 16 — recaps + types | `domain/cycle-recaps.md` | **landed** `f5aa402` |
| 17 — alertes + polish | `domain/cycle-recaps.md`, `domain/wizard-ui.md` ; briefs `core-richer-alerts.md`, `infra-richer-alerts.md`, `ui-richer-alerts.md` | **landed** `f5e2e67` (UI v0.16.0) |
| 18 — warn-fr | `domain/cycle-recaps.md` ; briefs `core-warn-fr.md`, `infra-warn-fr.md` | **landed** `3e910dc` |
| 19 — exemple-snapshot | `domain/exemple-snapshot.md` ; briefs `core-exemple-snapshot.md`, `infra-exemple-snapshot.md`, `ui-exemple-snapshot.md` | **landed** `7e4547a` (UI v0.17.0) |
| 20 — UI polish | `domain/wizard-ui.md` ; brief `ui-polish.md` | **landed** `15869b5` (UI v0.18.0) |
| 21 — export-config | `domain/export-config.md` ; briefs `infra-export-config.md`, `ui-export-config.md` | **landed** `9216c44` (UI v0.19.0) |
| 22 — export-planning | `domain/export-planning.md` ; brief `ui-export-planning.md` | **landed** `a3af6be` (UI v0.20.0) |
| 23 — admin | `domain/admin.md` ; briefs `infra-admin.md`, `ui-admin.md` | **landed** `db8d9e1` (UI v0.21.0) |
| 24 — coerce-railway | `domain/coerce-railway.md` ; brief `infra-coerce-railway.md` | **landed** `e5b13a3` |
| 25 — generate-jobs + polish UI | `domain/generate-jobs.md`, `http/v1-generate.md`, `domain/export-planning.md`, `domain/wizard-ui.md` ; briefs `infra-generate-jobs.md`, `ui-planning-polish.md` | **landed** `71b6bfa` (UI v0.22.0) |
| 26 — versions + chrome | `domain/generate-versions.md` ; briefs `infra-generate-versions.md`, `ui-planning-chrome.md` | **landed** `2ef7548` (UI v0.23.0) |
| 27 — admin recap + wizard polish | `domain/admin.md`, `domain/generate-versions.md`, `domain/wizard-ui.md` ; briefs `infra-admin-recap.md`, `ui-wizard-polish.md` | **landed** `881876e` (UI v0.24.0) |
| 28 — notes /10 | `domain/score.md` ; briefs `core-score.md`, `infra-score.md`, `ui-score.md` | **landed** `782b694` (UI v0.25.0) |
| 29 — score chrome | `domain/score.md` ; briefs `core-score-chrome.md`, `infra-score-chrome.md`, `ui-score-chrome.md` | **landed** `a6f0baa` (UI v0.26.0) |
| 30 — score gauges | `domain/score.md` ; briefs `core-score-gauges.md`, `ui-score-gauges.md` | **landed** `6ad338f` (UI v0.27.0) |
| 31 — banc admin | `domain/bench.md` ; briefs `core-bench.md`, `infra-bench.md`, `ui-bench.md` ; `data/bench/` | **landed** `fa24a33` (UI v0.28.0) |
| 32 — crafted + chrome banc | `domain/bench.md` ; briefs `core-bench-crafted.md`, `infra-bench-crafted.md`, `ui-bench-crafted.md` | **landed** `cad892b` (UI v0.29.0) |
| 33 — score facts | `domain/score-facts.md` + patches score / recaps / snapshot / admin / export / generate / sandbox ; briefs `core-score-facts.md`, `infra-score-facts.md`, `ui-score-facts.md` | **landed** `dfe7810` (UI v0.30.0) |
| 34 — banc recap + pack | `domain/bench.md`, `domain/score.md` ; briefs `core-bench-pack.md`, `infra-bench-pack.md`, `ui-bench-pack.md` | **landed** `0dfc765` (UI v0.31.0) |
| 35 — score tables | `domain/score-facts.md`, `domain/score.md`, `domain/cycle-recaps.md` ; brief `ui-score-tables.md` | **landed** `5b21221` (UI v0.32.0) |
| 36 — banc versions | `domain/bench.md` ; briefs `core-bench-versions.md`, `infra-bench-versions.md`, `ui-bench-versions.md` | **landed** `fc1f8cb` (UI v0.33.0) |
| 37 — banc tableau versions | `domain/bench.md` ; brief `ui-bench-table-versions.md` | **landed** `84e0a9b` (UI v0.34.0) |
| 38 — plafonds durs | `domain/wellbeing.md` ; brief `core-max-services-hard.md` | **landed** `e10a434` (Core `core-1`) |
| 39 — fill fewest | `domain/wellbeing.md` ; brief `core-fill-fewest.md` | **landed** `72d9174` (Core `core-2`) |
| 40 — banc élargi | `domain/bench.md` ; brief `core-bench-widen.md` (Infra/UI ensuite) | **freeze** — pas landé |

## Ownership git (ne pas croiser)

| Zone | Owner |
|---|---|
| `contracts/` | orchestrateur |
| `openspec/specs/` + archive `2026-09-04-define-planning-core` + `src/doux_planning/` hors `api/` | Core |
| `openspec/changes/preview-sandbox-edits/` | Core (Python preview/apply/undo) |
| `openspec/changes/build-planning-api/` + `src/doux_planning/api/` + Compose / migrations | Infra |
| `openspec/changes/build-planning-ui/` + `web/` | UI |

Interdit : `/opsx-archive`, `/opsx-sync`. Spécialistes commit + push **leur** branche (pas `master`). Orchestrateur land Core → Infra → UI (`--no-ff`).
