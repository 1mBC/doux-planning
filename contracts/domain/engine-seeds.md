# Moteur `core-3` — seeds → SAT → fill

Freeze **Core**. Keep-best **inchangé** : `_attempt_key` = `(empty, interdit, hours_miss, souhait, below_role, overqual)`.  
`weekend-eve` / `eve-first` **reportés** (pas cette file).

`engine_ref` = `trim(data/bench/VERSION)` → **`core-3`**.

## Pipe

```
seeders → shifts verrouillés
       → SAT repos (contraint par les locks)
       → fill des trous (locks intouchables)
       → keep-best sur tous les (seed × calendrier)
```

Un **seed** = liste de `Shift` **lock**. SAT force `work[emp, jour] = 1` sur ces jours et réduit le besoin de couverture des services déjà tenus.  
Fill / `_repair_holes` / displace **ne bougent pas** un lock (même tuyau que le préremplissage client, plus tard).  
Seed qui rend le SAT hard **infeasible** → **jeté** (0 calendrier), pas de slack.

## T = 3 (seuil tendu)

Constante `SEED_TIGHT_THRESHOLD = 3`.

Une fenêtre (jour × service × poste) est **tendue** si le nombre de fiches qui **peuvent** la tenir (`_can_fill_window`, grille considérée) est **≤ 3**.

Exemple : samedi soir, 2 éligibles → on seed. Mardi midi, 8 éligibles → on ne seed pas, SAT + fill s’en chargent.

## Seeders

| id | Règle |
|---|---|
| `tight-frozen` | Éligibles **une fois** grille vide. Seed seulement les fenêtres `eligible ≤ 3`, fewest d’abord. |
| `tight-dynamic` | Même seuil 3, mais on **recalcule** les éligibles après chaque pose. Prochaine = la plus tendue encore `≤ 3`. |
| `high-role` | Postes L6 puis L5… d’abord (tous), tension ensuite. |
| `weekend-scarce` | Samedi / dimanche fewest d’abord (seuil 3). |
| `empty` | Zéro shift = pipe `core-2`. **Une seule** copie (10× empty = le même départ). |

**Qui on pose** (fenêtre à seed) :

1. légal (`_can_fill_window` + locks déjà là)
2. niveau **exact** (pas d’overqual)
3. le **moins versatile** (le moins d’autres fenêtres encore vides qu’il peut tenir)
4. le plus loin de ses heures contrat
5. `employee_id`

**Copies** d’un même seeder (10 / 50) : même règle, diversité = permutation des fenêtres à égalité + tirage parmi candidats à égalité (`seed_index`). Sans ça, N copies = 1 seed.

## Fill — plus de « déjà posé aujourd’hui »

Aujourd’hui `_soft_penalty` a `int(not started_day)` : ça **favorise** celui qui a déjà un shift le même jour (ça **crée** des coupures midi/soir).

`core-3` : **retirer** cette préférence. À la place : **pénaliser** un trial qui **crée une coupure** (déjà un shift ce jour-là **et** un trou entre les deux). Préférer quelqu’un sans shift ce jour, ou un enchaînement sans trou.

Le plafond dur `max_coupures_per_week` reste un skip (`_would_exceed_coupures`). Fewest-first (`core-2`) **reste** l’ordre des fenêtres à fill. Locks seed : intouchables.

## Compute

`SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` inchangés : 16 / 320 / ∞ et 3 s / 30 s / 600 s.

| effort | Seeds | SAT |
|---|---|---|
| `minimal` | `empty` only (0 seeder) | 16 calendriers, comme `core-2` |
| `optimized` | 10 × chaque seeder **sauf** `empty` (×1) | **320** unique **round-robin** 1 / seed, deadline 30 s |
| `maximal` | 50 × chaque (empty ×1) | round-robin, **stop 10 min** |

Round-robin : on ne vide pas le budget sur le seed 1. Keep-best sur **tous** les essais.

## Tests

- `engine_ref() == "core-3"`.
- `minimal` : aucun lock, 16 calendriers max, `_already_on_day` ne favorise plus.
- Un lock pose `work=1` ; fill ne le déplace pas.
- Seed infeasible → ignoré, les autres continuent.
- `run_bench(tight, halles, minimal)` vert. Catalogue 50 **inchangé**.
- Keep-best / `_attempt_key` **bit-à-bit** la même clé.

## Hors freeze

Préremplissage HTTP client (Infra plus tard). `weekend-eve`. Archive / sync.
