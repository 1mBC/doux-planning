# Moteur `mix-0` — mixture of experts

Freeze **Core** (+ ETA bench = brief Infra). Module **nouveau** `engines/mix_0.py`. Pas live (VERSION reste `core-5`).

Keep-best **interne** de chaque expert **inchangé**. Catalogue 50 **inchangé**.  
`SEARCH_SECONDS` des autres moteurs **inchangé** (3 / 30 / 600).

`engine_ref` = `mix-0`.

## Liste figée (v0)

```
MIX0_EXPERTS = ("core-2", "core-2.1", "cp-0", "iter-0")
```

Constante dans le module. **Pas** de param HTTP. Une prochaine version (`mix-1`) = une autre liste figée.

Ordre d’appel = cet ordre. `mix-0` **ne s’appelle pas** lui-même. `iter-0` appelle déjà `core-5` en interne : c’est voulu (style seeds+repair ≠ fewest).

## Deux scores (le mixeur)

**Keep-best** (`_attempt_key`) = tuple **lexicographique** pour choisir un calendrier **dans** un moteur :

`(empty, interdit, hours_miss, souhait, below_role, overqual)`

Le premier écart gagne. Un planning 0 trou + 4 repos cassés **bat** 4 trous + 0 interdit.

**Globale** = moyenne pondérée des notes /10 (couverture 3, légal 3, contrat 2, wellbeing 1,5, rôles 0,5). C’est **la note du banc**.

**`mix-0` choisit l’expert à la globale** (`cycle_score.global`, 1 décimale).  
Égalité de globale → `_attempt_key` (comme aujourd’hui) → ordre `MIX0_EXPERTS`.

Chaque expert continue d’utiliser **son** keep-best en interne.

## Pipe

```
pour expert dans MIX0_EXPERTS :
    result, trace = generate_for(expert, draft, search, budget)
garder le result à globale max
```

Séquentiel. Un seul planning en sortie = celui du gagnant.

### Budgets temps

| Appel `mix-0` | Chaque expert |
|---|---|
| `minimal` | son `minimal` natif (3 s, 16 calendriers) — mur ≈ **12 s** |
| `optimized` | son `optimized` natif (30 s, 320 calendriers) — mur ≈ **120 s** |
| `maximal` | pipe **maximal** de l’expert (calendriers illimités) mais **deadline = 600 / 4 = 150 s** chacun. Reste éventuel → dernier expert. Mur = **600 s** |

Minimal / optimized : **somme** des efforts natifs (pas un cap 3 s / 30 s sur tout le mix).  
Maximal : les 10 min sont **partagées**, pas 4 × 10 min.

Implémentation libre : override `SEARCH_SECONDS` / timeout solveur le temps de l’appel expert, puis restore.

## SearchTrace (mix-0)

```
{
  seeder: "mix",
  seed_index: 0,
  n_locks: 0,
  calendars_by_seeder: { "mix": 1 },
  calendars_total: 1,
  seeds_infeasible: 0,
  attempt_key: { … },          # celui du gagnant
  repairs: null,
  mix: {
    experts: ["core-2", "core-2.1", "cp-0", "iter-0"],
    picker: "global",
    winner: "core-2",
    runs: [
      { engine_ref, global, attempt_key, duration_seconds }
    ]
  }
}
```

`SearchTrace` live : champ optionnel `mix: dict | None = None`. `registry.generate_for` **copie** `mix` (comme `repairs`).

## Registre

Ajouter `mix-0` **après** `iter-0`.

`generate_for("mix-0", …)` → `engines/mix_0.generate_cycle`.  
`_CUSTOM_TRACE_ENGINES` inclut `mix-0`.

## Infra (ETA)

Un job bench `engine_ref=mix-0` :

- `minimal` / `optimized` : plafond ETA = `len(MIX0_EXPERTS) * SEARCH_SECONDS[effort]`
- `maximal` : 600 s (inchangé)

Sinon le loader croit 30 s alors que mix-0 optimized tourne ~2 min.

## Tests

- `list_engine_refs()` finit par `…, "iter-0", "mix-0"`.
- `run_bench(tight, halles, minimal, engine_ref="mix-0")` : tourne, `trace.mix.winner` ∈ MIX0_EXPERTS, `trace.mix.runs` a 4 entrées, 0 hang.
- Gagnant = l’expert à globale max (égalité → attempt_key).
- `MIX0_EXPERTS` ne contient pas `mix-0`.
- Pytest vert.

## Hors freeze

`mix-1` autre liste. Picker keep-best. Parallèle. Exclure mix-0 des `gaps`. Live VERSION.
