# Contrats d’interface

Propriétaire : **orchestrateur** (chat Tech Lead).  
Core, UI et Infra **lisent** ces fichiers. Ils ne les modifient pas. Un champ manquant = stop, remonter au facteur, ne pas inventer.

OpenSpec (`openspec/changes/…`) décrit le comportement métier.  
Ce dossier fige les **shapes HTTP** (routes, clés JSON, invariants). En cas de conflit de forme, ce dossier gagne.

## Tranches

| Tranche | Fichier | Consommateurs |
|---|---|---|
| 0 — exemple public | `http/v1-examples.md` | UI + Infra |
| 1 — auth | (pas encore, sautée pour le joujou édition) | — |
| 2 — édition sandbox | `http/v1-sandbox-edit.md` | Infra + UI (HTTP actuel) |
| 3 — feedback overlay | `http/v1-sandbox-edit.md` + briefs `*-refine-sandbox-feedback.md` | fait |
| 4 — rôle / downrole | `http/v1-sandbox-edit.md` (`impact.role_fit`) | swap = créneau cliqué (pas la somme des deux) |
| 5 — case vide | `http/v1-sandbox-edit.md` (`gesture: fill`) | fait |
| 6 — fin sandbox | `http/v1-sandbox-edit.md` (`discard` + recap `history`) ; brief `infra-sandbox-close.md` | Infra d’abord |

## Ownership git (ne pas croiser)

| Zone | Owner |
|---|---|
| `contracts/` | orchestrateur |
| `openspec/specs/` + archive `2026-09-04-define-planning-core` + `src/doux_planning/` hors `api/` | Core |
| `openspec/changes/preview-sandbox-edits/` | Core (Python preview/apply/undo) |
| `openspec/changes/build-planning-api/` + `src/doux_planning/api/` + Compose / migrations | Infra |
| `openspec/changes/build-planning-ui/` + `web/` | UI |

Interdit à tous : `/opsx-archive`, `/opsx-sync`, commit / push / PR sauf demande du facteur.
