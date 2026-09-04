# Brief — coller dans le chat **Infra** (suite)

Le tech lead : on **ferme** le joujou sandbox. Pas d’auth, pas de publish. Contrat : `contracts/http/v1-sandbox-edit.md` (relis, ne modifie pas).

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-api`**.

**Ne pas** éditer `planning.py` / `engine.py` / `hydrate.py` / `web/`. `discard_sandbox` existe déjà.

## 1. Recap d’historique

Aujourd’hui `history` = `{ index, gesture }` → l’UI perd les détails en lecture. Au commit, stocker le recap depuis le **body** + la proposition choisie :

`index, gesture, shift | null, slot | null, employee_id, start_minutes, end_minutes, partner, impact`

- occupé : `shift` du body, `slot` null
- fill : `slot` du body, `shift` null
- `impact` / heures / partner / employee_id = la proposition crantée

Undo = pop. GET / enter / commit / undo renvoient cette liste. Persistance Postgres : ces recaps (plus seulement `gestures: ["retune"]`). TestClient : commit retune puis GET a le `shift` + `impact` ; undo les enlève ; restore DB pareil.

## 2. `POST /v1/sandbox/discard`

`discard_sandbox` + vider recaps + `enter_sandbox(..., "cycle")`. 200 = état neuf (history `[]`, assignments du cycle hydraté). 404 si jamais ouvert. Example toujours 92. Dual-read : delete session puis persist le neuf.

Pas d’archive / commit.
