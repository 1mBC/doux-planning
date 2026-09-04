# Brief — coller dans le chat **Infra** (suite, pas une première intro)

Le tech lead : Core a **fini** `preview-sandbox-edits` (Python). Tranche 0 exemple toujours valable. On **ne** enchaîne **pas** tes tâches 2–5 de `build-planning-api` (auth, jobs, adapters génériques).

**Lis (ne pas modifier) :** `contracts/http/v1-sandbox-edit.md` et `contracts/http/v1-examples.md`. Conflit de forme → le contrat gagne.

**Mission :** nouveau change OpenSpec `sandbox-edit-api`. Skills `.cursor/skills/openspec-*` → propose **puis** `/opsx-apply` (le contrat HTTP est déjà figé par l’orchestrateur ; tes artifacts doivent le refléter, pas l’élargir).

Wrap **uniquement** :

- `hydrate_delivered_cycle` / `PlanningStore.enter_sandbox(..., "cycle")`
- `preview_retune` / `preview_replace` / `preview_swap`
- `apply_proposal` / `undo_sandbox`

Routes du contrat : `POST /v1/sandbox/enter`, `GET /v1/sandbox`, `POST /v1/sandbox/preview`, `POST /v1/sandbox/commit`, `POST /v1/sandbox/undo`.

**Coupes**

- Pas d’auth. Saint-Cloud hydraté.
- `GET /v1/examples/saint-cloud` inchangé ; dual-read fichier si pas de `DATABASE_URL`.
- Pas de week vs cycle dans l’API. Pas de websocket. Pas de `generate_cycle`. Preview ne mute pas.
- Commit = rejouer preview + matcher la proposition (ne pas inventer un `proposal_id` volatile).
- Undo = un pop. 409 si pile vide, message français.
- Ne pas éditer `planning.py` / `engine.py` / `hydrate.py` / `web/` / l’archive V0.
- Code nouveau sous `api/` + migrations si persist Postgres quand `DATABASE_URL` est là.
- Étendre les tests existants (`TestClient`), pas un nouveau fichier d’exemple JSON.
- Pas d’archive `/opsx-archive` ni `/opsx-sync`. Pas de commit.

Si le 200 exemple casse ou s’il faut changer une clé du contrat sandbox : **stop**.
