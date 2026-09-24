# Moteurs figés (banc)

Freeze **Core**. `core-5` = `engine.py` live. Pas de fichier `VERSION`.  
Live resto **client** (POST generate) = `live_engine_ref` admin (`admin.md`), repli = dernier de `list_engine_refs()` (`bench-engine-choice.md` **gagne**).  
Banc peut rejouer d’anciens `engine_ref` **sans** checkout git.

Keep-best / `_attempt_key` **inchangés**. Pipe seeds = `core-3` (`engine-seeds.md`).  
Fill live = `engine-core-5.md`. Fill `core-6` = `engine-core-6.md`. Catalogue 50 **inchangé**.

## Registre

```
src/doux_planning/engines/
  core_0.py      # generate_cycle figé
  core_1.py
  core_2.py
  core_2_1.py    # fill fewest + repair empty posts (peut voler un repos)
  core_2_2.py    # repair légal +4 h
  core_2_3.py    # titulaires jusqu’à 48 h
  core_2_4.py    # ouvreurs / fermeurs 11 h
  core_2_5.py    # réserves petits contrats
  core_2_6.py    # week-ends, contrat, surplus, fenêtre exacte
  core_3.py
  core_4.py
  core_6.py      # seeds + recase rares (jamais live)
  mix_0.py       # mixture of experts
  registry.py    # list_engine_refs / generate_for
```

| `engine_ref` | Source | SHA `engine.py` |
|---|---|---|
| `core-0` | `engines/core_0.py` | `dd23c4b81fc2d88769b36273e414281ff3d03aca` |
| `core-1` | `engines/core_1.py` | `420cd6b452dfd9123e99e0210f90270be194ebfc` |
| `core-2` | `engines/core_2.py` | `f34ff3b2d0e998c4fa568f4ca3d0d7161c3bab72` |
| `core-2.1` | `engines/core_2_1.py` | fill fewest + repair (`engine-core-2-1.md`) |
| `core-2.2` | `engines/core_2_2.py` | repair légal (`engine-core-2-2.md`) |
| `core-2.3` | `engines/core_2_3.py` | titulaires 48 h (`engine-core-2-3.md`) |
| `core-2.4` | `engines/core_2_4.py` | 11 h ouvreurs/fermeurs (`engine-core-2-4.md`) |
| `core-2.5` | `engines/core_2_5.py` | réserves ≤ 8 h (`engine-core-2-5.md`) |
| `core-2.6` | `engines/core_2_6.py` | week-ends, contrat, surplus, fenêtre exacte (`engine-core-2-6.md`) |
| `core-3` | `engines/core_3.py` | `3167392bd974be8da70cb1a23274ed2675cc7ead` |
| `core-4` | `engines/core_4.py` | `da1ef781ef572eb3eb30cde97060dd31788f79b5` |
| `core-5` | `engine.py` **live** | registre, pas un fichier |
| `core-6` | `engines/core_6.py` | nouveau (pas un snapshot live) |
| `cp-0` | `engines/cp_0.py` | CP-SAT global (`engine-cp-0.md`) |
| `iter-0` | `engines/iter_0.py` | post-traitement itératif (`engine-iter-0.md`) |
| `mix-0` | `engines/mix_0.py` | mixture (`engine-mix-0.md`) |

`list_engine_refs()` = ces ids, ordre du tableau. Inconnu → `UnknownEngineRef`.  
`generate_for(ref, draft, search)` → `(EngineResult, SearchTrace)`.

Copie du `engine.py` à ce SHA (adapter le package), **sauf** `core-6` (écrit d’après `engine-core-6.md`). Imports `types` / `staff` / `coverage` / `warnings` **live**. Chaque module expose `generate_cycle(draft, search)`.

`generate_team(state, team, search, engine_ref=None)` : omis = dernier de `list_engine_refs()` ; sinon `generate_for`. Pas un 2ᵉ fill HTTP.

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

`core-0` / `core-1` / `core-2` / `core-2.6` : `seeder="empty"`, `seed_index=0`, `n_locks=0`, `calendars_by_seeder={ "empty": N }`, `seeds_infeasible=0`. `core-2.6` n’est pas dans `MIX0_EXPERTS`.  
`core-2.1` : idem + `repairs` **nichés dans** `attempt_key` (historique).  
`core-2.2` / `core-2.3` / `core-2.4` / `core-2.5` : `repairs` **à la racine** du trace. `SearchTrace.repairs` optionnel.  
`mix-0` : `seeder="mix"` + `mix: { experts, picker, winner, runs }` (`engine-mix-0.md`). `SearchTrace.mix` optionnel.  
`core-3` / `core-4` / live `core-5` / `core-6` : **`result.trace`** du keep-best (seeder gagnant, locks, calendriers **remplis** par seeder, seeds jetés) — pas le stub empty.

`run_bench(..., engine_ref=)` pose `outcome.engine_ref` et `outcome.trace`. Omis → dernier de `list_engine_refs()`.

## Tests

- `list_engine_refs() == ("core-0","core-1","core-2","core-2.1","core-2.2","core-2.3","core-2.4","core-2.5","core-2.6","core-3","core-4","core-5","core-6","cp-0","iter-0","mix-0")`.
- `run_bench("tight","halles", minimal)` et `engine_ref="core-0"`…`"mix-0"` : 0 interdit expected, `trace` complète, `outcome.engine_ref` = demandé.
- `core-2` **n’appelle pas** les seeders (pas de locks).
- `core-3` figé : pipe seeds `engine-seeds.md` (anti-coupure **toujours**).
- `core-4` figé : fill `engine-core-4.md`.
- `core-5` explicite : pipe seeds, fill `engine-core-5.md`, `trace.seeder` renseigné.
- Omis (`run_bench` / `generate_team`) : dernier de `list_engine_refs()` (aujourd'hui `mix-0`), pas le fill `core-5`.
- `core-6` : pipe seeds, fill `engine-core-6.md`, `trace.seeder` renseigné.
- Ref inconnue → `UnknownEngineRef`.
- Pas de `engine_ref()`. Pas de fichier `VERSION`. 50 jeux. Keep-best inchangé.

## Hors freeze

Relance qui **écrase** un run déjà tracé. Archive / sync.
