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
| 14 — seed exemple | `domain/example-seed.md` ; brief `core-example-seed-push.md` | Core à pousser ; puis Infra HTTP |

## Ownership git (ne pas croiser)

| Zone | Owner |
|---|---|
| `contracts/` | orchestrateur |
| `openspec/specs/` + archive `2026-09-04-define-planning-core` + `src/doux_planning/` hors `api/` | Core |
| `openspec/changes/preview-sandbox-edits/` | Core (Python preview/apply/undo) |
| `openspec/changes/build-planning-api/` + `src/doux_planning/api/` + Compose / migrations | Infra |
| `openspec/changes/build-planning-ui/` + `web/` | UI |

Interdit à tous : `/opsx-archive`, `/opsx-sync`, commit / push / PR sauf demande du facteur.
