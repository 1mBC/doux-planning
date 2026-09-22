# Brief — agent Infra neuf (cloud) · change **admin-historique** (file 70)

Le tech lead : **note /10** sur le log generate, **GET planning actuel** d’un resto, **lien impersonate copiable**. Relis `contracts/domain/admin-historique.md` (**gagne**) + `admin.md` / `v1-auth.md`. Tu ne modifies **pas** `contracts/`.

**Pas de Core.** File 71/72 **hors scope** (pas d’import banc, pas de delete, pas de `…`).

Instance **neuve**. Branche **`cursor/admin-historique-infra-2843`** depuis **master** (freeze `admin-ops` déjà mergée). **Ne merge pas** `master`. **Ne pas** réécrire Core / `web/`.

`/opsx-update` **`build-planning-api`**. Nouveau change OpenSpec **`admin-historique`** si besoin (propose + apply HTTP). Pas d’archive / sync.

**Alembic OK** : `generate_logs.restaurant_id` + `score_global` + table `impersonate_tokens`. Révision après `20260921_0016`.

**Ne pas toucher** `web/`, `engine.py`, `contracts/`, `data/bench/`. Reste `api/` + Alembic.

**Process** : pytest vert → **commit + push**. Message : `feat(api): admin generate note, view planning, impersonate link`. Signal le SHA.

## Comportement

- `_log_generate` persiste `restaurant_id` + `score_global` (globale du slot).
- GET `/v1/admin/generates` : clés toujours là, null si vieux.
- GET `/v1/admin/restaurants/{id}/cycles` et `/context` = même JSON que les GET company de ce resto. 404 inconnu.
- POST `/v1/admin/impersonate` `{ restaurant_id }` → `{ url, expires_at }` TTL 15 min.
- POST `/v1/auth/impersonate` `{ token }` public → session company, one-shot. 2ᵉ fois 401 `Lien expiré ou déjà utilisé.`
- SPA FastAPI : `/impersonate/{token}`, `/admin/planning/{restaurant_id}` → `index.html`.

## Tests

`skipif` sans `DATABASE_URL`. Generate 200 → log a les deux champs. GET admin les émet. GET cycles admin == GET cycles company (même published). Impersonate mint + consume + 2ᵉ 401. Session admin d’origine intacte. Non-admin 403. 404 resto. Pytest api **nouveaux** verts ; échecs préexistants Saint-Cloud / engine-ref **inchangés** (ne pas « corriger »).

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra admin-historique pushed @ <sha>`
