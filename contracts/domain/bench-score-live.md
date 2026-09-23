# Note banc = note du planning ouvert

Freeze **domaine**. File 76. Gagne sur `bench.md` pour la source de `score` d’un run.  
Core uniquement (`run_bench_on`). Infra HTTP et UI **inchangés**. File 74 (versions légères) **reste**.

## Bug

Sur le banc, relancer mix-0 (ex. extrait importé LE GARDE MANGER) met à jour les créneaux : clic « voir » montre le nouveau planning. La case du tableau **ne bouge pas**. La pastille /10 sur la page du run **a augmenté**.

Deux sources :

| Surface | Source aujourd’hui |
|---|---|
| Tableau / Stats (`GET /versions` `cell.global`) | JSON `bench_runs.score` gelé au persist |
| Page run (`GET /runs/{id}` `model.score`) | `evaluate` **live** (`engine.py`) + `cycle_recap_from_draft` sur les créneaux persistés |

`run_bench_on` note le généré avec les `warnings` du moteur appelé (mix-0 = evaluate **vendored** du gagnant). La page re-note avec `engine.py`. Après leftover / 11 h / every_two, la re-note live monte ; le snapshot persisté non.

Le tableau n’affiche **pas** la globale /10 (`bench.md`) : meilleur = delta vs Manuel ×10 ; sinon écart vs le meilleur. Si `cell.global` persisté ne change pas, la case non plus.

## Règle

Après `generate_for`, **re-noter** le cycle généré comme la page run :

1. `model_draft = draft.with_assignments(result.assignments)`
2. `scored = evaluate(model_draft)` — `evaluate` live (`engine.py`), **pas** les `warnings` du générateur / expert mix-0
3. `recap = cycle_recap_from_draft(model_draft, scored)`

`outcome.score`, `outcome.facts`, `outcome.warnings` = ce recap / `scored.warnings`.  
`outcome.assignments` = créneaux **générés** (inchangés).  
`outcome.engine_ref` = ref **demandée** (mix-0 reste mix-0, pas le gagnant).  
Oracle : déjà `evaluate` live — inchangé.

`GET /versions` continue de lire `bench_runs.score` (file 74 : ne pas charger `assignments`). Un **nouveau** run écrit la globale live → la case suit. Vieux rows : relancer.

Picker mix-0 (`cycle_score` interne pour choisir l’expert) **inchangé**.

## Hors scope

- Recalculer toutes les cellules `GET /versions` à la volée (trop lourd).
- Afficher la note /10 dans le tableau (déjà tranché : delta ×10).
- Infra persist / UI / Alembic / `engine.py` formules / leftover.
- Re-noter les rows déjà en base sans nouveau compute.

## Tests

`run_bench_on` (jeu catalogue `minimal`, au moins un `engine_ref` vendored ex. `core-2` **et** `mix-0`) : `outcome.score.global_score` égal à `cycle_recap_from_draft(draft.with_assignments(outcome.assignments), evaluate(...)).score.global_score`.
