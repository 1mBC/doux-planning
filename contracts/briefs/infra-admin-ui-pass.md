# Brief — agent Infra neuf (cloud) · change **admin-ui-pass** (file 73)

Le tech lead : **SPA Banc Manuels** + **`origin`** sur lancer / export. Relis `contracts/domain/admin-ui-pass.md` Infra (**gagne**). Tu ne modifies pas `contracts/`.

**Pas de Core.** **Pas de `web/`.** Pas d’Alembic. HTTP DELETE / import / impersonate **intouchés**.

Instance **neuve**. Branche **`cursor/admin-ui-pass-infra-2843`** depuis **master**. **Ne merge pas** `master`.

`/opsx-update` **`build-planning-api`**. Nouveau change OpenSpec **`admin-ui-pass`** si besoin. Pas d’archive / sync.

**Process** : pytest vert → **commit + push**. Message : `feat(api): bench origin on run/export and SPA /admin/bench/manuels`. Signal le SHA.

## Comportement

- `SPA_PATHS` : `/admin/bench/manuels` → `index.html` (comme `/admin/bench`).
- `POST /v1/admin/bench/run` body `origin` optionnel `"catalogue"` | `"imported"`.
  - Filtre `scope=all` | `category` | `gaps`.
  - Absent / null / `""` → les deux origines (comportement actuel).
  - `scope=dataset` : `origin` ignoré.
  - Valeur inconnue → 400 `Champs invalides.`
- `GET /v1/admin/bench/export` query `origin` pareil pour `below_manuel` et `bank`. `dataset` : ignoré.
- `/versions` inchangé. Tombstones toujours exclus. Cuisine-only exclus des all/gaps comme aujourd’hui.

## Tests

`skipif` sans `DATABASE_URL`. SPA manuels sert index si `dist` (skip sinon). Après import : `scope=all` + `origin=catalogue` n’enqueue pas l’importé ; `origin=imported` n’enqueue pas le catalogue. `gaps` + `origin=catalogue` sans job importé. Sans `origin` = les deux. `origin=nope` 400. Export `bank&origin=catalogue` sans dataset imported. 403 non-admin. Échecs préexistants Saint-Cloud / engine-ref **non corrigés**.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra admin-ui-pass pushed @ <sha>`
