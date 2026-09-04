# Brief — coller dans le chat **UI** (suite)

Le tech lead : **Infra a fini.** `impact.role_fit` est dans le JSON (`contracts/http/v1-sandbox-edit.md`). Liste 0 ou 1 : `{ current_gap, trial_gap, kind: "better" | "worse" }`.

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-ui`**. Uniquement `web/`. Pas de score calculé. Pas de `src/doux_planning/`. Pas d’archive / commit.

Aujourd’hui le parseur **ignore** `role_fit` : il faut le typer, le parser, l’afficher. Liste vide = rien (comme un contrat inchangé).

## Affichage (les trois gestes)

Dans `HoursImpact` **et** `SwapReplaceImpact` (retune sera presque toujours vide, replace/swap c’est le cas).

- `better` → vert : **poste plus proche du niveau (−N)** avec `N = current_gap - trial_gap`
- `worse` → rouge : **surqualification +N** avec `N = trial_gap - current_gap`

N vient des champs API, pas d’un recalcul niveau/poste. « Aucun impact listé » seulement s’il n’y a vraiment rien (y compris `role_fit` vide).

IronBee : replace sur un poste bas, une ligne verte ou rouge selon le candidat ; candidat même niveau = pas de ligne rôle.
