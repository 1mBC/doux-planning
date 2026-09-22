# Brief — agent Infra neuf (cloud) · change **bench-chrome** (file 72)

Le tech lead : **DELETE jeu + résultats**, tombstone catalogue. Relis `contracts/domain/bench-chrome.md` Infra (**gagne**). Tu ne modifies pas `contracts/`.

**Attends** file 71 landé (table importés + `origin`). Instance **neuve**. Branche **`cursor/bench-chrome-infra-2843`** depuis **master**. **Ne merge pas** `master`. Pas de Core. Pas de `web/`.

`/opsx-update` **`build-planning-api`**. Alembic : `bench_tombstones`.

**Process** : pytest vert → **commit + push**. Message : `feat(api): delete bench dataset and tombstone catalogue`. Signal le SHA.

## Comportement

- `DELETE /v1/admin/bench/datasets/{category}/{id}` → 204. Importé : drop row+runs+jobs. Catalogue : tombstone + drop runs+jobs, fichiers intacts. 2ᵉ DELETE 204.
- `/versions` / gaps / all / export : **pas** les tombstones.
- 404 inconnu. 403 non-admin.

## Tests

`skipif` sans DB. Delete importé disparu. Delete halles disparu de la liste, dossier `data/bench/tight/halles` encore là. Gaps ne le requeue pas. 404 junk. Échecs préexistants non corrigés.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-chrome pushed @ <sha>`
