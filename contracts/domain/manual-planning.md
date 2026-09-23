# Planning manuel (4ᵉ slot)

Freeze **domaine + HTTP + UI**.  
Gagne sur `generate-versions.md` / `v1-generate.md` / `live-sandbox.md` / `v1-live-sandbox.md` pour le cran **manuel**.

Le restaurateur compose un cycle **à la main** depuis `/planning`, cran **Manuel** à côté de Minimal / Optimisé / Maximal. Mêmes overlays que l’édition d’un cycle calculé (fill / retune / replace / swap). Notes + facts se mettent à jour **après chaque commit**, overlay d’impact au clic. **Pas** de solve.

`SearchEffort` moteur (`minimal` | `optimized` | `maximal`) et le banc **inchangés**. `manuel` est une **clé de slot publié**, pas une hypothèse de calendriers.

## Décisions figées

1. 4ᵉ slot `versions.manuel`, indépendant. Un generate n’écrase **pas** ce slot.
2. Départ = **grille vide** (types + fiches de l’équipe, zéro assignment). Pas une copie d’un calcul. Éditer un calcul = rester sur Minimal/Optimisé/Maximal + « Entrer en mode édition ».
3. Publier le manuel **tamponne `generated_at` = maintenant** et `latest` se recalcule (le manuel devient `latest` s’il est le plus récent). Les salariés voient `versions[latest]`. Un generate **plus tard** peut reprendre `latest` ; le slot `manuel` reste.
4. Score = édition actuelle : overlay au clic, **notes + facts après commit** (pas de jauge live au survol).
5. Publier incomplet autorisé (postes vides = warnings, pas de blocage).
6. Pas de « tout vider » en v1. Discard = dernier **publié** manuel, ou vide s’il n’y en a jamais eu.
7. Publish manuel **n’écrit pas** `generate_logs`.

## Core

`RestaurantState.published_cycles` reste **un** `PublishedCycle` par équipe (le multiplex 4 slots est Infra).

```
seed_empty_team_cycle(state, team) -> PublishedCycle
```

- `team_ready` faux → `TeamNotReady`. **Aucun** `generate_cycle` / `generate_for`.
- Même squelette que `generate_team` : `expand_typical_week` filtré équipe + fiches de l’équipe + `hours` + `default_legal_rules()`.
- `assignments = ()`. `result = evaluate(draft)` (coverage / legal / contrat / wellbeing — surtout `empty_post`).
- Écrit `published_cycles[team]` (copie de travail mémoire). L’autre équipe intacte.
- `SearchEffort` enum **intouché**. `draft.search_effort` = défaut existant (pas de membre `MANUEL`).

`enter_live_sandbox` / `discard_live_sandbox` / `publish_live_sandbox` **inchangés** : enter exige un publié (le seed le pose) ; publish réécrit ce publié ; discard jette le brouillon.

Gestes : **réutiliser** `preview_*` / `apply_proposal` / `undo_sandbox`. Pas de nouveau geste. Pas de formules / FIFO / keep-best.

Saint-Cloud `state.sandbox` + `hydrate` + `/v1/sandbox/*` **intouchés**.

Tests : resto + salle ready, **sans** `generate_team` → `seed_empty_team_cycle` : assignments vides, `evaluate` a des empty_post, cuisine `published_cycles` intact (`None`). Enter + fill + apply + undo comme `test_live_sandbox` (sur ce seed). `TeamNotReady` si pas ready. `generate_team(..., minimal)` ensuite remplace le **slot Core** salle (comportement existant). Saint-Cloud verts. **Interdit** d’appeler `generate_cycle` dans le chemin manuel.

## Infra HTTP

Clés de slot : `minimal` | `optimized` | `maximal` | `manuel`.

```
versions: {
  minimal: Cycle | null,
  optimized: Cycle | null,
  maximal: Cycle | null,
  manuel: Cycle | null
}
latest: "minimal"|"optimized"|"maximal"|"manuel"|null
```

Coerce : blob à 3 clés → `manuel: null`. Plat ancien → toujours `versions.optimized` + `manuel: null`. GET **émet toujours** les 4 clés. Pas d’Alembic (JSONB).

`Cycle` manuel : assignments + facts + recap + `search_effort: "manuel"` + `generated_at`. **Pas** `duration_seconds`. **Pas** `engine_ref`.

`latest` = `generated_at` le plus récent ; égalité : `manuel` > `maximal` > `optimized` > `minimal`.

`POST /v1/generate` avec `search_effort: "manuel"` → 400 `Champs invalides.` Generate n’écrit que `minimal|optimized|maximal`. Recalcule `latest` (peut quitter `manuel`). Slot `manuel` intact.

```
POST /v1/live/sandbox/{team}/enter
  body/query { "search_effort": "minimal"|"optimized"|"maximal"|"manuel" }
```

- `manuel` + slot **null** : `TeamNotReady` → 409 `Cette équipe n'est pas prête à calculer.` Sinon Core `seed_empty_team_cycle` puis enter. Persist **brouillon live seulement** — `versions.manuel` reste `null` jusqu’au publish.
- `manuel` + slot déjà publié : hydrate ce slot, enter (ré-enter = même brouillon).
- Compute + slot vide → 409 `Aucun cycle publié pour cette équipe.` (inchangé).
- Défaut enter sans effort = `latest` ; si `latest` null et on demande manuel explicitement → seed vide (ci-dessus).

`POST .../publish` si le brouillon est le slot **manuel** : écrit `versions.manuel`, **`generated_at` = maintenant** (chaque publish, contrairement au keep-`generated_at` des calculs), `search_effort: "manuel"`, sans durée / moteur, `latest` recalculé, ferme le brouillon. **Pas** d’insert `generate_logs`. Autres slots / autre équipe intacts.

`POST .../discard` : Core discard puis re-enter **le même** slot. Manuel jamais publié → re-seed vide, history vide.

Preview / commit / undo : **mêmes routes et shapes**. Infra wrappe, ne rescore pas.

Banc : `EFFORTS` **reste** les 3 computes.

## UI

`/planning` company, rangée 2 :

`Minimal | Optimisé | Maximal | Manuel`

Cran **Manuel** :

- **Pas** de bouton (Re)Calculer.
- `ctx.ready[team]` → **Entrer en mode édition** même si `versions.manuel` est null.
- Slot vide, hors édition : « Pas encore publié » (pas « Pas encore calculé »).
- Édition : `POST enter` `{ search_effort: "manuel" }` + **mêmes** Overlay / FillOverlay / undo / discard / publish que le live actuel.
- Publier / quitter / historique : inchangés.
- Timestamp : `generated_at` Paris ; pas de ` · engine_ref` ; durée `—`.

Cran compute : inchangé (Recalculer + édition ssi cycle non null).

Parser cycles : 4ᵉ clé ; absente → `null` (Infra pas encore mergé). `postGenerate` **jamais** appelé avec `manuel`. Banc : `BENCH_EFFORTS` reste 3 ; ne pas parser `manuel` comme effort banc.

`/exemple` et `/me/planning` (lecture `latest`, pas de sélecteur) inchangés côté chrome. `/admin` historique : pas de ligne generate pour un publish manuel.

`web/src/release.ts` + `package.json` : **0.55.0**, note FR : `Planning manuel`.

## Hors freeze

Admin « voir le planning » / impersonation. Drag-drop. Quart d’heure. Nouveaux gestes. Reset vider. `generate_logs` manuel. `SearchEffort.MANUEL` dans le moteur. Banc. Jobs. Archive / sync. Saint-Cloud joujou.
