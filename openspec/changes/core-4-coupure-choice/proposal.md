## Why

Banc `core-3` vs `core-2` : mixte. Les gros reculs (postes vides, surtout échelles / 2 L6 / cadres) existent déjà en minimal (`empty`, 16 calendriers). Cause : le fill pénalise toute coupure (midi déjà posé + trou avant le soir), même quand personne d'autre ne peut tenir le poste. Les seeds aident d'autres jeux (jours fermés, tight) — on les garde.

Phrase resto : on ne laisse pas un service à découvert pour protéger le confort d'une fiche s'il n'y a personne d'autre.

## What Changes

- Fill : anti-coupure seulement s'il y a le choix. Parmi les fiches encore légales pour cette fenêtre : s'il existe au moins une fiche pour qui `_creates_coupure` est faux → il y a le choix, le composant `int(creates_coupure)` s'applique. Sinon → composant coupure vaut 0 pour tout le monde. On couvre le poste.
- Ne pas ramener `int(not started_day)` (`core-2` poussait à recaser le même, même équipe large).
- `_creates_coupure` inchangé. `max_coupures_per_week` skip inchangé. Fewest-first inchangé. Locks seed : intouchables.
- Snapshot du live `core-3` → `engines/core_3.py`. `data/bench/VERSION` → `core-4`. `list_engine_refs` = `core-0` … `core-4`. Live `engine.py` = `core-4`.

## Capabilities

### Modified Capabilities

- `core-engine`: fill pénalise coupure seulement quand une alternative sans coupure existe.

## Impact

- `src/doux_planning/engine.py` : `_soft_penalty` et `_pick_for_post` ajustés pour le choix coupure.
- `src/doux_planning/engines/core_3.py` : snapshot figé de l'ancien live.
- `src/doux_planning/engines/registry.py` : ajoute `core-3` figé et `core-4` live.
- `data/bench/VERSION` : `core-4`.
- Tests moteur. Catalogue 50 jeux bit-à-bit. Pas de `web/`, `api/`, `contracts/`.
