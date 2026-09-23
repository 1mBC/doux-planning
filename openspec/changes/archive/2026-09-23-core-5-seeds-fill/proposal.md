## Why

`core-4` (anti-coupure seulement s'il y a le choix) = no-op vs `core-3` sur le banc. Les gros reculs vs `core-2` (postes vides, échelles, 2 L6, cadres) viennent du fill qui refuse de recaser la même personne midi + soir. Les seeds aident d'autres jeux — on les garde.

`core-5` : recase **tout le monde** comme `core-2`, après les seeds.
`core-6` : recase **seulement les rares** (poste que presque personne d'autre ne peut tenir).

## What Changes

### core-5 (live engine.py)
- Snapshot core-4 → engines/core_4.py
- VERSION → core-5
- Fill : remettre `int(not started_day)`, retirer `int(creates_coupure)` et `coupure_matters`
- Seeds pipe inchangé

### core-6 (nouveau module engines/core_6.py)
- Même pipe seeds que core-3
- Fill : si candidat rare → `int(not started_day)` (recase) ; sinon → `int(creates_coupure)` (pas de stack)
- Rare = existe au moins une fenêtre vide du cycle avec ≤ 3 éligibles dont le candidat
- SearchTrace réelle (pas stub empty)

### Registry
- list_engine_refs = core-0 … core-6
- generate_for : core-3/core-4/core-6 → result.trace réelle
- generate_team(..., engine_ref=) omis = VERSION ; sinon generate_for

## Capabilities

### Modified Capabilities
- `core-engine`: fill core-5 préfère le déjà-là ; core-6 recase les rares seulement

## Impact

- `src/doux_planning/engine.py` : `_soft_penalty` simplifié core-5
- `src/doux_planning/engines/core_4.py` : snapshot figé
- `src/doux_planning/engines/core_6.py` : nouveau module
- `src/doux_planning/engines/registry.py` : core-0..core-6, traces
- `src/doux_planning/context.py` : generate_team engine_ref
- `data/bench/VERSION` : core-5
- Tests moteur. Pas de web/, api/, contracts/.
