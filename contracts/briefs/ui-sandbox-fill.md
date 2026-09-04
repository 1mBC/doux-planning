# Brief — coller dans le chat **UI** (suite)

Le tech lead : **Infra a fini.** `POST /v1/sandbox/preview` `gesture: "fill"` est live. Contrat : `contracts/http/v1-sandbox-edit.md`. Swap `role_fit` sur le créneau cliqué est déjà dans le JSON (l’échange doit montrer vert/rouge — vérifie en IronBee).

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-ui`**. Uniquement `web/`. Pas de score calculé. Pas d’heures inventées (pas de 10h en dur). Pas de `src/doux_planning/`. Pas d’archive / commit.

## Case vide

Aujourd’hui `onOccupiedClick` seulement, et « rest » ne fait rien. En édition, clic sur une case **vide** (Emma × lundi × matin) → overlay **fill**, pas les 3 gestes occupés.

`weekday` API = `monday`…`sunday` (`day_index % 7`). **Pas** « Lundi ». `team` = `person.team`. `service_id` = `midday` | `evening`.

1. Ouverture : `preview` `{ gesture: "fill", slot, start_minutes: null, end_minutes: null }`.
2. Curseur ±15 **après** la 200 : début/fin = `proposals[0].start_minutes/end_minutes` (Saint-Cloud matin = 10h–16h). Chaque pas → mêmes `slot` + heures **après** le pas (les deux nombres, plus de null).
3. Haut : personne **ligne** (rang 1 si le moteur la met en 1) + son `impact` + **Valider**.
4. Dessous : les **autres** `proposals` (ordre `rank`), titre = nom, même `impact` que replace. Clic = commit cette personne.
5. Commit : `{ gesture: "fill", slot, employee_id, start_minutes, end_minutes }` (heures du preview, pas null). History : libellé français pour `fill` (ex. « Créneau posé »).
6. 409 → `detail` français, overlay ouvert, grille inchangée.

Pas de recalcul niveau/poste. `role_fit` fill = souvent `[]` : normal. IronBee : case vide Emma lundi matin → overlay, 10h–16h, liste en dessous, Valider Emma, undo.
