# Brief — coller dans le chat **Core Engine** (suite)

Le tech lead (orchestrateur) valide le recap v0.4.11 / GitHub Pages. On change de slice.

**Lis** `contracts/README.md`. Tu n’y touches pas. Tu n’touches pas `web/`, `src/doux_planning/api/`, `contracts/http/`. `GET /v1/examples/saint-cloud` et le snapshot `data/examples/saint-cloud.json` restent le contrat **figé** (seed / démo) : tu peux **lire** ce planning pour hydrater un draft, tu ne le réécris pas comme bac à sable.

## Mission

Nouveau change OpenSpec (nom suggéré : `preview-sandbox-edits`). Skills `.cursor/skills/openspec-*` → **explore puis propose**. **Pas d’implémentation** avant OK. Pas de `/opsx-archive` ni `/opsx-sync`. `define-planning-core` reste ouvert ; tu n’y empiles pas ce slice (nouveau change).

Objectif produit : à partir d’un planning **déjà livré par le moteur** (hydrater Saint-Cloud / le cycle actuel dans un `PlanningStore`), le restaurateur entre en **mode édition** et teste des changements avec **feedback avant de cranter**.

Le sandbox Python existe déjà (`enter_sandbox`, `apply_edit`, `generate_into_sandbox`, `swap_shifts`, `rank_candidates` sur créneau **vide**). Ce slice ajoute ce qui manque pour l’UI plus tard. **Pas de HTTP. Pas de React.**

## Coupes (ne pas rouvrir)

- Cible interne = sandbox **cycle**. Pas d’UX ponctuel vs croisière ; ne pas demander week vs cycle.
- **Preview ≠ apply.** Un geste d’abord : résultat moteur + delta d’impact, draft inchangé. Puis apply (crante dans le sandbox + entrée d’historique).
- Auth / HTTP / overlay : hors scope (Infra / UI après un contrat).
- Undo = **pile** (annuler le dernier, éventuellement dépile en reculant). Pas d’undo d’un geste au milieu.
- Un seul score = `evaluate` / ranking existants. Pas de second scorer. Ordre des propositions = l’ordre moteur actuel (interdit, puis souhait, etc.). Ne « corrige » pas le FIFO / keep-best que tu viens de poser.
- Messages warnings = sortie moteur. Le delta = warnings ajoutés / retirés / inchangés par rapport au draft courant (ids/codes), pas un nouveau diagnostic rédigé.

## Gestes à specker (Python)

1. **Retune horaires** d’un shift existant (début et/ou fin), grille 15 min, même `service_id` / jour / personne. Preview = liste de propositions d’horaires candidates (borne raisonnable, ex. ±2 h autour de l’actuel, quantum 15 min, durée ≥ `min_shift_hours`) chacune avec `EngineResult` + delta. Apply = un de ces horaires.
2. **Remplacer la personne** sur un créneau **occupé** (`rank_candidates` actuel ignore les occupés et sert un trou vide — il faut retirer le titulaire puis classer les autres sur cette fenêtre).
3. **Échanger** ce créneau avec un autre shift (réutiliser `swap_shifts`). Preview = partenaires candidates classés + impact. Apply = un swap.

Chaque proposition preview : assez pour qu’un overlay affiche rang, personne ou nouvel horaire, warnings du résultat, delta vs draft actuel.

Historique d’edits crantés sur le sandbox + `undo` qui restaure l’état précédent (assignments + last_result).

Hydratation : construire un `RestaurantState` + cycle publié + sandbox cycle depuis le planning Saint-Cloud **livré** (staff + structures + hours + assignments du snapshot), sans rappeler `generate_cycle` pour ça.

## Interdit

- Modifier `api/`, `web/`, `contracts/`, le HTML GitHub Pages, sauf si un test d’hydratation lit `data/` en **lecture**.
- Archiver / sync OpenSpec.
- Commit / push / PR.
- Inventer des routes HTTP ou des champs « pour le front ».

Si un doute produit ou moteur : demander. Quand les artifacts (proposal / design / specs / tasks) sont prêts, tu t’arrêtes et tu attends la validation.
