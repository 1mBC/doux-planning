# Brief — coller dans le chat **Infra** (suite)

Le tech lead : Core ajoute `impact.role_fit` (`RoleFitImpact` : `current_gap`, `trial_gap`, `kind` `better`|`worse`). Le champ est déjà sur `PreviewImpact` dans `planning.py`. Contrat : `contracts/http/v1-sandbox-edit.md` (relis, ne modifie pas).

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-api`**. Pas d’auth/jobs.

**Ne pas** éditer `planning.py` / `engine.py` / `hydrate.py` / `web/`. Si `role_fit` disparaît du Python : stop, ne l’invente pas.

- Sérialiser `impact.role_fit` (liste, 0 ou 1 objet) dans `_impact_json`. Reste de l’impact inchangé.
- TestClient replace : un cas où `role_fit` est `better` ou `worse` selon le moteur ; un cas liste vide si égal. Ne pas recalculer les gaps dans l’adapter.
- Exemple public 92 assignments. Dual-read. Pas d’archive, pas de commit.

`tests/test_preview_sandbox.py` est partagé : tu n’ajoutes que des cas HTTP ; tu ne réécris pas les tests Python Core.
