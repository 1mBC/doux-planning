# Moteurs figés (banc)

Freeze **Core**. Live resto = `engine.py` / `VERSION` (`core-3`).  
Banc peut rejouer d’anciens `engine_ref` **sans** checkout git. Pas de 2ᵉ fill dans `POST /v1/generate`.

Keep-best / `_attempt_key` / pipe seeds **inchangés**. Catalogue 50 **inchangé**.

## Registre

```
src/doux_planning/engines/
  core_0.py      # generate_cycle figé
  core_1.py
  core_2.py
  registry.py    # list_engine_refs / generate_for
```

| `engine_ref` | Source | SHA `engine.py` |
|---|---|---|
| `core-0` | `engines/core_0.py` | `dd23c4b81fc2d88769b36273e414281ff3d03aca` |
| `core-1` | `engines/core_1.py` | `420cd6b452dfd9123e99e0210f90270be194ebfc` |
| `core-2` | `engines/core_2.py` | `f34ff3b2d0e998c4fa568f4ca3d0d7161c3bab72` |
| `core-3` | `engine.py` **live** | `VERSION` |

`list_engine_refs()` = ces ids, ordre du tableau. Inconnu → `UnknownEngineRef`.  
`generate_for(ref, draft, search)` → `(EngineResult, SearchTrace)`.

Copie du `engine.py` à ce SHA (adapter le package). Imports `types` / `staff` / `coverage` / `warnings` **live**. Chaque module expose `generate_cycle(draft, search)`.

Plus tard `core-4` : snapshot du live → `engines/core_3.py`, puis on avance `VERSION`. **Pas** cette file.

## `SearchTrace`

Toujours renvoyé (jamais null sur un run neuf) :

```
{
  seeder: str,                 # "empty" si pas de seeds
  seed_index: int,
  n_locks: int,
  calendars_by_seeder: { str: int },
  calendars_total: int,
  seeds_infeasible: int,
  attempt_key: {
    empty, interdit, hours_miss, souhait, below_role, overqual
  }
}
```

`core-0` / `core-1` / `core-2` : `seeder="empty"`, `seed_index=0`, `n_locks=0`, `calendars_by_seeder={ "empty": N }`, `seeds_infeasible=0`.  
Live `core-3` : valeurs réelles du keep-best (seeder gagnant, locks de ce seed, calendriers **remplis** par seeder, seeds jetés).

`run_bench(..., engine_ref=)` pose `outcome.engine_ref` et `outcome.trace`. Omis → `VERSION`.

## Tests

- `list_engine_refs() == ("core-0","core-1","core-2","core-3")`.
- `run_bench("tight","halles", minimal)` et `engine_ref="core-0"|"core-1"|"core-2"` : 0 interdit expected, `trace` complète, `outcome.engine_ref` = demandé.
- `core-2` **n’appelle pas** les seeders (pas de locks).
- `core-3` / omis : pipe seeds inchangé, `trace.seeder` renseigné.
- Ref inconnue → `UnknownEngineRef`.
- `engine_ref() == "core-3"`. 50 jeux. Keep-best inchangé.

## Hors freeze

Snapshot `core-3` fichier (tant que c’est le live). Relance qui **écrase** un run déjà tracé. Archive / sync.
