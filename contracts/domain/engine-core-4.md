# Moteur `core-4` — anti-coupure seulement s’il y a le choix

**Figé.** Live = `contracts/domain/engine-core-5.md`. Snapshot `engines/core_4.py`.

Freeze **Core**. Pipe **`core-3` inchangé** (`contracts/domain/engine-seeds.md`) sauf le fill ci-dessous.

Keep-best **inchangé** : `_attempt_key` = `(empty, interdit, hours_miss, souhait, below_role, overqual)`.  
Catalogue 50 **inchangé**. `weekend-eve` / `eve-first` **reportés**.

`engine_ref` = **`core-4`** (plus `VERSION`).

## Pourquoi

Banc `core-3` vs `core-2` : mixte. Les gros reculs (postes vides, surtout échelles / 2 L6 / cadres) existent **déjà en minimal** (`empty`, 16 calendriers). Cause : le fill **pénalise toute coupure** (midi déjà posé + trou avant le soir), même quand **personne d’autre** ne peut tenir le poste. Les seeds aident d’autres jeux (jours fermés, tight) — **on les garde**.

## Fill — coupure s’il y a le choix

Ne **pas** ramener `int(not started_day)` (`core-2` poussait à recaser le même, même équipe large).

`_creates_coupure` **inchangé** : déjà un shift le même jour **et** un trou si on ajoute le trial.  
Plafond dur `max_coupures_per_week` : **skip** inchangé (`_would_exceed_coupures`).  
Fewest-first : inchangé. Locks seed : intouchables.

Parmi les fiches **encore légales** pour **cette** fenêtre (même filtre que le fill : `_can_fill_window` + skips durs, locks respectés) :

- S’il existe **au moins une** fiche pour qui `_creates_coupure` est **faux** → il y a le choix. Le composant `_soft_penalty` `int(creates_coupure)` **s’applique** (comme `core-3`).
- Sinon (une seule fiche légale, ou toutes feraient une coupure) → **pas le choix**. Le composant coupure vaut **0** pour tout le monde. On **couvre le poste**.

Les autres composants de `_soft_penalty` (caps, ratio heures, overqual, id) **inchangés**.

## Pipe / compute / seeds

Identiques à `engine-seeds.md` (T=3, 5 seeders, copies, round-robin, budgets 16 / 320 / 10 min).

## Registre

Snapshot du live `core-3` → `engines/core_3.py` (fait). Snapshot `core-4` → `engines/core_4.py` (file `core-5`).  
`list_engine_refs()` = `core-0` … `core-6`. Détail : `contracts/domain/engines.md`.

## Tests

- `generate_for("core-4", …)` joue ce fill. Live `engine_ref() == "core-5"`.
- `list_engine_refs()` contient `core-3` (figé, seeds) et `core-4` (figé).
- Deux légaux, un sans coupure : celui **avec** coupure est moins bien classé sur ce composant (`core-3`).
- Un seul légal qui ferait une coupure : **posé** (le poste n’est pas laissé vide pour ça).
- `run_bench(tight, halles, minimal, engine_ref="core-4")` vert. 50 listings. Keep-best bit-à-bit la même clé.

## Hors freeze

Budget SAT `empty` type `core-2` (hypothèse secondaire, pas la casse). Préremplissage HTTP. `weekend-eve`. Archive / sync.
