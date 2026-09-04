# Brief — coller dans le chat **Core Engine** (suite)

Le tech lead : deux corrects, **même** change. `/opsx-update` puis apply sur **`refine-sandbox-feedback`**. Pas de nouveau change. Relis `contracts/http/v1-sandbox-edit.md` (tu ne le modifies pas).

**Ne pas toucher** `web/`, `api/`, `contracts/`, FIFO / keep-best / `generate_cycle` / `_overqualification` / `occupied_sort_key` (sauf l’utiliser pour classer le fill). Pas de commit / archive.

## 1. Swap `role_fit` — créneau cliqué seulement

Aujourd’hui tu **sommes les deux postes**. Les écarts s’annulent → `role_fit` toujours vide à l’échange. C’est un trou, pas un hasard.

`current_slots` / `trial_slots` pour swap = **uniquement le `shift` preview** (comme replace), pas le partenaire. L4 sur poste 1 échangé avec un L2 ailleurs → `better` 3 → 1 sur **ce** poste. Deux mêmes niveaux sur ce poste → vide. Retune inchangé.

Mets à jour le test « swap somme inchangée → vide » : il ne décrit plus le cas utile. Cas : swap qui change le gap du poste cliqué → une ligne ; swap qui ne le change pas → vide.

## 2. Case vide = `preview_fill`

Emma lundi matin vide : on peut poser quelqu’un. **Pas** un overlay occupé.

`preview_fill(restaurant_id, slot, start_minutes | None, end_minutes | None)`  
`slot` : `employee_id` (la **ligne**), `day_index`, `weekday`, `service_id`, `team`.

- Heures None → span structure (`structure_for` : 1re arrivée → dernière départ). Sinon quantum 15, durée ≥ min de la personne d’essai, clip 0–1440.
- `post_level` = `role.level` de la personne **ligne** (le même poste pour tous les candidats de cet overlay).
- Si un assignment existe déjà pour ligne × jour × service → erreur occupé (pas un fill silencieux).
- Un `evaluate` par candidat (ajouter le shift, pas retirer). Draft inchangé.
- Liste : **d’abord** la personne ligne si `level >= post` et pas occupée sur le créneau ; **ensuite** les autres `rank_candidates` / même fenêtre, **sans** la ligne, tri `occupied_sort_key` vs draft courant.
- Impact comme les autres gestes. `role_fit` vide (pas d’occupant current). `gesture` `"fill"`. `employee_id` = le candidat. `start_minutes` / `end_minutes` sur chaque proposition.
- `apply_proposal` / undo inchangés (le trial a déjà les assignments).

Tests : ligne vide → Emma en rang 1, autres classés, draft intact ; heures None = span structure ; case déjà occupée → erreur ; fill + undo.

Tâches cochées + pytest vert → stop.
