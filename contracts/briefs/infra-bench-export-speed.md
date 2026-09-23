# Brief — agent Infra neuf (cloud) · change **bench-export-speed** (file 74)

Le tech lead : **export dataset = tous les moteurs** + **`GET /versions?origin=`** léger. Relis `contracts/domain/bench-export-speed.md` (**gagne**). Tu ne modifies pas `contracts/`.

**Pas de Core.** **Pas de `web/`.** Pas d’Alembic.

Instance **neuve**. Branche **`cursor/bench-export-speed-infra-2843`** depuis **master**. **Ne merge pas** `master`.

`/opsx-update` **`build-planning-api`**. Change OpenSpec **`bench-export-speed`** si besoin. Pas d’archive / sync.

**Process** : pytest vert → **commit + push**. Message : `feat(api): export dataset all engines and versions origin filter`. Signal le SHA.

## Comportement

- `scope=dataset` : last-runs **tous** `engine_ref` (comme un `bank` d’une ligne). 404 `Aucun run pour ce jeu.` ssi 0 row. Copied import (`trace=null`, engine resto) inclus. Ne plus utiliser `_latest_current_runs_map` ici. `below_manuel` inchangé (VERSION seulement).
- `GET /v1/admin/bench/versions?origin=catalogue|imported`. Absent = les deux. Inconnu 400 `Champs invalides.`
- `origin=imported` : pas de scan `data/bench/**`. `origin=catalogue` : pas de `list_imported_rows` / contextes importés.
- Versions : ne pas charger `assignments` / `warnings` / `trace` ni `bench_imported_datasets.context`.
- `engine_refs` = registre complet ∪ extras des runs filtrés.

## Tests

`skipif` sans DB. Import + computes `engine_ref` ≠ VERSION, pas de run VERSION → export dataset 200 efforts non vides. Catalogue 0 run → 404. versions origin filtre. origin=nope 400. Sans origin = les deux. 403. Échecs préexistants Saint-Cloud / engine-ref **non corrigés**.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra bench-export-speed pushed @ <sha>`
