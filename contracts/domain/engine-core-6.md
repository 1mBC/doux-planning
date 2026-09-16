# Moteur `core-6` — seeds + recase seulement les rares

Freeze **Core**. **Vendored** (`engines/core_6.py`), pas le live. Pipe **`core-3` inchangé** (`engine-seeds.md`) sauf le fill ci-dessous.

Keep-best **inchangé**. Catalogue 50 **inchangé**. `weekend-eve` **reporté**.

`engine_ref` = `core-6`. Pas `VERSION` (live = `core-5`).

## Pourquoi

`core-5` recase **tout le monde** (L1 compris) : ça remplit les échelles, ça peut recréer des coupures inutiles sur les petits contrats / 3 services.  
`core-3` / `core-4` ne recasent **personne** : les postes hauts restent vides.

Phrase resto : on recase midi+soir **seulement** quelqu’un dont on a vraiment besoin (il tient un poste que presque personne d’autre ne peut tenir). Un L1 interchangeable peut encore se répartir sur des jours différents.

## Personne rare

Au moment de scorer un candidat **E** (grille courante, locks déjà posés, fenêtres encore vides du **même** cycle / même équipe) :

**E est rare** ssi il existe **au moins une** fenêtre encore vide (tous jours × services de l’équipe, **y compris** celle qu’on remplit) telle que :

1. E `_can_fill_window` cette fenêtre
2. le nombre de fiches du pool qui `_can_fill_window` cette fenêtre est **≤ 3** (même T que les seeds)

Un L6 seul (ou à 2–3) sur un poste chef encore ouvert **est** rare. Un L1 parmi 8 éligibles sur des postes bas **n’est pas** rare.

## Fill

Ne **pas** utiliser `coupure_matters` (`core-4`). Fewest-first inchangé. Locks intouchables.  
`max_coupures_per_week` skip inchangé.

Dans `_soft_penalty`, à la place de `int(creates_coupure)` / `int(not started_day)`, **un** composant :

- si E **est rare** → `int(not started_day)` (`core-2` : on recase)
- sinon → `int(creates_coupure)` (`core-3` : on ne stack pas)

Les autres composants **inchangés**.

## Pipe / compute / seeds

Identiques à `engine-seeds.md`. `SearchTrace` **réelle** (comme `core-3` / live), pas le stub empty des `core-0`…`core-2`.

## Tests

- `generate_for("core-6", …)` + `run_bench(..., engine_ref="core-6")` : `outcome.engine_ref == "core-6"`, `trace.seeder` renseigné.
- Deux légaux sur une fenêtre **large** (plus de 3 éligibles, aucun rare) : celui qui **créerait** une coupure est moins bien classé.
- Deux légaux, l’un rare déjà posé ce jour, l’autre non : le **rare déjà là** est mieux classé.
- `run_bench(tight, halles, minimal, engine_ref="core-6")` vert. 50 listings. Keep-best inchangé.

## Hors freeze

Live `VERSION`. Picker admin (`admin.md`). `weekend-eve`. Archive / sync.
