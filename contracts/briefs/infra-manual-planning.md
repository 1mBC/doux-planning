# Brief — agent Infra neuf (cloud) · change **manual-planning**

Le tech lead : persist + HTTP **slot `manuel`**. Relis `contracts/domain/manual-planning.md` Infra **et** `contracts/http/v1-live-sandbox.md` / `v1-generate.md`. **Gagnent.** Tu ne modifies pas `contracts/`.

**Attends Core** : `seed_empty_team_cycle` doit être sur ta base (`cloud_base_branch` = branche Core). Si absent → **stop**, remonte.

Instance **neuve**. Branche **`cursor/manual-planning-infra-2843`**. **Ne merge pas** `master`. **Ne pas** réécrire Core.

`/opsx-update` **`build-planning-api`** (change `manual-planning` déjà proposé par Core). Pas d’archive / sync.

**Ne pas toucher** `web/`, `engine.py` formules, `contracts/`, `SearchEffort` enum, banc `EFFORTS` (reste 3). Reste `api/` + JSONB coerce. **Pas** d’Alembic.

**Process** : pytest vert → **commit + push**. Message : `feat(api): persist manual planning slot`. Signal le SHA.

## Comportement

- GET/POST cycles : toujours 4 clés dont `manuel`. Coerce 3 clés → `manuel: null`.
- `POST /v1/generate` `manuel` → 400. Generate n’écrit pas ce slot.
- Enter `search_effort=manuel` : slot null → seed Core + persist live **sans** écrire `versions.manuel` ; slot existant → hydrate. Team pas ready → 409 même detail generate.
- Publish du brouillon manuel : `generated_at` maintenant, pas duration/engine_ref, **pas** `generate_logs`, `latest` recalculé (`manuel` gagne à égalité de stamp).
- Discard manuel jamais publié → re-seed vide.

## Tests

`skipif` sans `DATABASE_URL`. Enter manuel sans generate → LiveState assignments vides + facts. Fill/commit. Publish → GET `versions.manuel` + `latest` manuel, generate_logs **pas** +1. Generate optimized ensuite → slot manuel intact. POST generate manuel 400. Cycles 3-clés coerce. Live/generate existants verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Infra manual-planning pushed @ <sha>`
