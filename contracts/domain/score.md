# Notes de cycle (/10)

Freeze **Core** (calcul). HTTP = brief Infra. Chrome + facts = `contracts/domain/score-facts.md` (gagne sur la forme d’affichage).  
**Pas** de changement du keep-best : `_attempt_key` / `SEARCH_*` / `generate_cycle` **inchangés**.

Une fonction, mêmes chiffres partout (recap, generate, bench) :

```
cycle_score(draft, result) -> CycleScore
```

Ou **dedans** `cycle_recap` (même objet). Pas de 2ᵉ solve. Lecture du cycle + fiches.

## Forme

```
CycleScore {
  notes: { couverture, legal, contrat, wellbeing, roles }  # float | null, 0–10, 1 décimale
  global: float | null
  weights: { couverture: 3, legal: 3, contrat: 2, wellbeing: 1.5, roles: 0.5 }
}
```

Toujours émettre les 5 clés de `notes`.  
**Plus de `resumes`.** L’UI compose les sous-lignes (`score-facts.md` Dictionnaire).  
`notes.*` `null` = axe omis (pas de dénominateur).  
`global` = moyenne **pondérée** des notes non null ; `null` si aucune note.  
Arrondi : `round(x, 1)` Python, clamp `[0, 10]`.  
`weights` = constantes (mémoire). **Pas** d’UI / PATCH restaurateur dans cette tranche.

Clé JSON `contrat` **inchangée**. Libellé UI : **Occupation**.

## Couverture

Même boucle que `empty_post` (tranches `derive_slices` × niveaux requis).

```
postes_requis = nombre de slots niveau requis sur le cycle
postes_vides  = stats.empty  (facts kind empty_post, polarity miss)
postes_tenus  = postes_requis − postes_vides
note = 10 × postes_tenus / postes_requis
```

`postes_requis == 0` → `couverture` null.

## Légal

Cellules **non null** de `legal_rows` seulement (tableau légal du recap).  
**Pas** les indispos.

```
note = 10 × (cellules ok) / (cellules)
```

Aucune cellule → `legal` null.

## Occupation (`notes.contrat`)

Deux sous-notes, moyenne des parties **présentes** :

1. **Heures** — par fiche avec `C = contractual_hours_per_week > 0`.  
   Sur-occupation **deux fois** plus sévère que la sous-occupation :

```
pen(h, C) = (C − h) / C           si h ≤ C
          = 2 × (h − C) / C       si h > C
pen_i     = pen(h_sem_A, C) + pen(h_sem_B, C)
note_i    = 10 × max(0, 1 − pen_i / 2)
heures    = moyenne des note_i
```

`h` = heures posées de **cette** semaine (même source que le recap / fact `contract_hours`).  
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

**Note /10 inchangée** — somme des écarts, **pas** le compteur `below_role` :

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

## UI

Chrome + **clic → liste facts** : `contracts/domain/score-facts.md` (gagne).  
**Même** `CycleScoreNotes` sur `/planning`, `/exemple`, banc compare.

Dans chaque pastille, ordre :

1. **titre** (Occupation /10, Globale /10, …)
2. **même ligne** : note + jauge (`note / 10`, HSL `hue = 12 × note`, `null` → jauge vide)
3. **ligne suivante** : totaux UI (`score-facts.md` résumés). Globale : pas de totaux.
4. clic → détail **miss puis hit**

- Rangée notes **au-dessus** de la grille (`/planning` company **et** `/exemple`).
- **Globale en premier à gauche.** Cadre **contrasté** vs les 5 axes.
- Tableaux légal / souhaits **sous** la grille.

## Tests

- Notes /10 **inchangées** (occupation ×2, rôles = écart / plafond).
- Plus de `resumes` sur `CycleScore`.
- Keep-best inchangé. Exemple **92**.

## Hors freeze

Keep-best / `_attempt_key`. Poids éditables. Archive / sync.
