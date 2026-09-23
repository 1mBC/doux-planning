# Moteur `core-5` — seeds + fill « déjà là aujourd’hui »

Freeze **Core**. Pipe **`core-3` inchangé** (`contracts/domain/engine-seeds.md`) sauf le fill ci-dessous.

Keep-best **inchangé** : `_attempt_key` = `(empty, interdit, hours_miss, souhait, below_role, overqual)`.  
Catalogue 50 **inchangé**. `weekend-eve` / `eve-first` **reportés**.

`engine_ref` = `trim(data/bench/VERSION)` → **`core-5`**. Live `engine.py`.

## Pourquoi

`core-4` (anti-coupure seulement s’il y a le choix) = **no-op** vs `core-3` sur le banc : le fill `core-3` posait déjà la dernière chaise.  
Les gros reculs vs `core-2` (postes vides, échelles, 2 L6, cadres) viennent du fill qui **refuse de recaser** la même personne midi + soir. Les seeds aident d’autres jeux (jours fermés, tight) — **on les garde**.

Phrase resto : coller midi et soir la personne **déjà posée aujourd’hui**, comme `core-2`, **après** les seeds.

## Fill — préférence `core-2`

Ne **pas** garder `int(creates_coupure)` ni `coupure_matters` (`core-3` / `core-4`).

Remettre dans `_soft_penalty`, **à la même place** que `int(creates_coupure)` aujourd’hui :

`int(not started_day)` — `started_day` = `_already_on_day` (déjà un shift ce `day_index`).

Plus bas = mieux : on **préfère** celui qui a déjà un service ce jour-là.

Plafond dur `max_coupures_per_week` : **skip** inchangé (`_would_exceed_coupures`).  
Fewest-first : inchangé. Locks seed : intouchables.  
Autres composants `_soft_penalty` (caps, ratio heures, overqual, id) **inchangés**.

## Pipe / compute / seeds

Identiques à `engine-seeds.md` (T=3, 5 seeders, copies, round-robin, budgets 16 / 320 / 10 min).

## Registre

Snapshot du live `core-4` → `engines/core_4.py` (SHA `engine.py` `da1ef781ef572eb3eb30cde97060dd31788f79b5` @ `044b61e`).  
Live `engine.py` = `core-5`. `list_engine_refs()` = `core-0` … `core-6` (détail `engines.md` ; `core-6` = `engine-core-6.md`).

`generate_team(..., engine_ref=)` : omis → `VERSION`. Dispatch `generate_for`. Inconnu → `UnknownEngineRef`.

## Tests

- `engine_ref() == "core-5"`.
- `list_engine_refs()` = `core-0` … `core-6`.
- Deux légaux, un déjà posé ce jour : celui **déjà là** est mieux classé sur ce composant (`core-2`).
- `run_bench(tight, halles, minimal)` vert. `engine_ref="core-4"` joue le snapshot. 50 listings. Keep-best bit-à-bit la même clé.
- `generate_team(..., engine_ref="core-2")` n’appelle pas les seeders.

## Hors freeze

`core-6` fill (fichier à part). Préremplissage HTTP. `weekend-eve`. Archive / sync.
