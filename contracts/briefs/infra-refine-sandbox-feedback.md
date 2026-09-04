# Brief — coller dans le chat **Infra** (suite)

Le tech lead : Core a fini `refine-sandbox-feedback` (73 tests). Le contrat HTTP **change** : `contracts/http/v1-sandbox-edit.md` (relis-le, ne le modifie pas).

**Casse** : `preview_retune(restaurant_id, shift)` n’existe plus. C’est `preview_retune(id, shift, start_minutes, end_minutes)` → 0 ou 1 proposition. `IdentityRetuneError` si mêmes heures.

**Mission :** `/opsx-update` puis apply sur `sandbox-edit-api` (pas un nouveau mega-change, pas les tâches auth/jobs). Adapter `api/sandbox.py` + tests TestClient. **Ne pas** éditer `planning.py` / `engine.py` / `hydrate.py` / `web/`.

- Preview retune : exiger `start_minutes` + `end_minutes` dans le body.
- Replace/swap : listes inchangées côté routes, mais sérialiser `impact` + `current_score` / `trial_score` (tuple `_attempt_key` → objet du contrat). Plus de `delta` ni de `warnings` plein trial sur une proposition.
- GET/enter : ajouter `score` du draft courant (`_attempt_key` sur last_result — import adapter OK).
- 400 français identité / durée min. Commit retune = re-preview avec les heures choisies.
- `partner` JSON : tous les champs Shift y compris `day_index` / `weekday`.
- Exemple public 92 assignments. Dual-read. Pas d’archive, pas de commit.

Si le Python n’a pas le champ : stop, ne l’invente pas.
