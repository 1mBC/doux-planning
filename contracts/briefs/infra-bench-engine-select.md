# Brief Infra — file 61 sélecteur moteur bench

**Freeze** : `contracts/domain/bench.md` @ master tip.

## Objectif

Permettre de choisir le moteur lors d'un lancement bench via l'API.

## Modification

`POST /v1/admin/bench/run` — ajouter un champ **optionnel** `engine_ref` dans le body.

### Comportement

1. **Absent ou vide** : utiliser `engine_ref()` (VERSION) — comportement actuel inchangé.
2. **Présent et valide** (`engine_ref in list_engine_refs()`) : utiliser ce moteur pour les jobs.
3. **Présent mais invalide** : 400 `{ "detail": "engine_ref inconnu" }`.

### Code concerné

`src/doux_planning/api/bench.py` :
- `_parse_run_body` : extraire `engine_ref` du body, valider contre `list_engine_refs()`.
- `post_run` : utiliser le `engine_ref` validé au lieu de `engine_ref()` pour `_enqueue_bench_job`.

### Exemple body

```json
{
  "scope": "all",
  "search_effort": "optimized",
  "engine_ref": "core-2"
}
```

### Tests

- `POST { scope: all, effort: minimal }` sans `engine_ref` → utilise VERSION (core-5).
- `POST { scope: all, effort: minimal, engine_ref: "core-2" }` → jobs avec `engine_ref="core-2"`.
- `POST { scope: all, effort: minimal, engine_ref: "inconnu" }` → 400.
- `POST { scope: gaps }` ignore `engine_ref` (comportement inchangé, remplit tous les refs).

## Hors scope

UI (brief UI séparé).
