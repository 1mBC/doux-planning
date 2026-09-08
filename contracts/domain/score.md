# Notes de cycle (/10)

Freeze **Core** (calcul). HTTP = brief Infra ensuite. UI pastilles = brief UI.  
**Pas** de changement du keep-best : `_attempt_key` / `SEARCH_*` / `generate_cycle` **inchangés**.

Une fonction, même chiffres partout (recap, generate, bench plus tard) :

```
cycle_score(draft, result) -> CycleScore
```

Ou **dedans** `cycle_recap` (même objet). Pas de 2ᵉ solve. Lecture du cycle + fiches.

## Forme

```
CycleScore {
  notes: {
    couverture: float | null,   # 0–10, 1 décimale
    legal:      float | null,
    contrat:    float | null,
    wellbeing:  float | null,
    roles:      float | null
  }
  global: float | null
  weights: { couverture: 3, legal: 3, contrat: 2, wellbeing: 1.5, roles: 0.5 }
}
```

Toujours émettre les 5 clés. `null` = axe omis (pas de dénominateur).  
`global` = moyenne **pondérée** des notes non null ; `null` si aucune note.  
Arrondi : `round(x, 1)` Python, clamp `[0, 10]`.  
`weights` = constantes (mémoire). **Pas** d’UI / PATCH restaurateur dans cette tranche.

## Couverture

Même boucle que `empty_post` (tranches `derive_slices` × niveaux requis).

```
postes_requis = nombre de slots niveau requis sur le cycle
postes_vides  = stats.empty  (warnings code empty_post)
note = 10 × (postes_requis − postes_vides) / postes_requis
```

`postes_requis == 0` → `couverture` null.

## Légal

Cellules **non null** de `legal_rows` seulement (tableau légal du recap).  
**Pas** les indispos.

```
note = 10 × (cellules ok) / (cellules)
```

Aucune cellule → `legal` null.

## Contrat

Deux sous-notes, moyenne des parties **présentes** :

1. **Heures** — par fiche avec `C = contractual_hours_per_week > 0` :

```
miss_i = |h_sem_A − C| + |h_sem_B − C|
note_i = 10 × max(0, 1 − miss_i / (2C))
heures = moyenne des note_i
```

Aucune fiche avec `C > 0` → pas de sous-note heures.

2. **Indispos** — cellules `wish_rows[*].cells.indispo` non null :

```
indispo = 10 × (ok) / (cellules)
```

Aucune cellule indispo → pas de sous-note indispo.

```
contrat = moyenne des sous-notes présentes
```

Les deux absentes → `contrat` null.

## Bien-être

`stats.wellbeing` **tel quel** (contrat / indispo **hors** ce compteur) :

```
note = 10 × held / total
```

`total == 0` → `wellbeing` null.

## Rôles (sous-roling)

Somme des écarts, pas le compteur `below_role` :

```
ecarts   = Σ (level_fiche − post_level)     # _overqualification
plafond  = Σ max(0, level_fiche − 1)        # par shift
note     = 10 × (1 − ecarts / plafond)
```

`plafond == 0` (pas de shift, ou tous niveau 1) → `roles` null.

## Globale

```
global = Σ (poids × note) / Σ poids des axes non null
```

Poids ci-dessus. Axe `null` : exclu du dénominateur.

## Hors freeze

Keep-best / `_attempt_key`. Poids éditables. Bench admin. Rewrite `saint-cloud.json`. Archive / sync.
