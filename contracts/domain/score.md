# Notes de cycle (/10)

Freeze **Core** (calcul + `resumes`). HTTP = brief Infra. Chrome UI = brief UI.  
**Pas** de changement du keep-best : `_attempt_key` / `SEARCH_*` / `generate_cycle` **inchangés**.

Une fonction, même chiffres partout (recap, generate, bench plus tard) :

```
cycle_score(draft, result) -> CycleScore
```

Ou **dedans** `cycle_recap` (même objet). Pas de 2ᵉ solve. Lecture du cycle + fiches.

## Forme

```
CycleScore {
  notes: { couverture, legal, contrat, wellbeing, roles }  # float | null, 0–10, 1 décimale
  resumes: { mêmes clés: string | null }                   # une ligne FR qui explique la note
  global: float | null
  weights: { couverture: 3, legal: 3, contrat: 2, wellbeing: 1.5, roles: 0.5 }
}
```

Toujours émettre les 5 clés de `notes` **et** les 5 de `resumes`.  
`notes.*` `null` = axe omis (pas de dénominateur) → `resumes.*` `null`.  
`global` = moyenne **pondérée** des notes non null ; `null` si aucune note. Pas de `resumes.global`.  
Arrondi : `round(x, 1)` Python, clamp `[0, 10]`.  
`weights` = constantes (mémoire). **Pas** d’UI / PATCH restaurateur dans cette tranche.

Clé JSON `contrat` **inchangée**. Libellé UI : **Occupation** (pas « Contrat », pas « Taux d’occupation »).

## Couverture

Même boucle que `empty_post` (tranches `derive_slices` × niveaux requis).

```
postes_requis = nombre de slots niveau requis sur le cycle
postes_vides  = stats.empty  (warnings code empty_post)
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

`h` = heures posées de **cette** semaine (même source que le recap / warning `contract_hours`).  
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

## Résumés (`resumes`)

Une phrase FR par axe, **exactement** ces formes, `null` si la note est `null`.  
Heures = même forme que `_hours_label` (`29h` / `11h30`). Entiers pour les comptes.

- couverture : `{tenus} / {requis} postes tenus`
- legal : `{ok} / {n} règles tenues`
- contrat : parties présentes jointes par ` · `
  - heures : `{h_posées} / {h_contrat} contrat`  
    `h_posées` = `stats.hours.assigned` (14 j.) ; `h_contrat` = `stats.hours.contracted` (somme `C × 2`)
  - indispo : `{ok} / {n} indispos tenues`
- wellbeing : `{held} / {total} souhaits tenus`
- roles : `écart {ecarts} / {plafond}`

## Globale

```
global = Σ (poids × note) / Σ poids des axes non null
```

Poids ci-dessus. Axe `null` : exclu du dénominateur.

## UI (cette tranche)

Chrome seulement — **pas** de 2ᵉ formule.

- Rangée notes **au-dessus** de la grille, **avant** tout autre bloc stats (`/planning` company **et** `/exemple`).
- Libellé `notes.contrat` : **Occupation /10**. Autres : Couverture / Légal / Bien-être / Rôles / Globale, tous `/10`.
- Sous chaque pastille d’axe : `resumes[clé]` tel quel. Globale : pas de sous-ligne.
- Couleur **linéaire continue** 0→10 : teinte HSL `hue = 12 × note` (0 = rouge, 120 = vert). Pas de seuils / buckets. `null` → neutre (tiret, pas de teinte).
- **Retirer** les cartes `CycleStats` / `Stats` (shifts, vides, alertes, sous-rôle, % heures, souhaits).  
  Tableaux `LegalRecap` / `WishRecap` **inchangés**, **sous** la grille.

## Tests

- Même écart `|h − C|` : sur-occupation note **stricement** plus basse que sous-occupation (`k = 2`).
- Fiche pile `C` les deux semaines → sous-note heures 10.
- `resumes` : 5 clés ; `null` ssi note `null` ; formes ci-dessus (sous-chaîne).
- Keep-best / `_attempt_key` inchangés. Exemple **92**.

## Hors freeze

Keep-best / `_attempt_key`. Poids éditables. Bench admin. Rewrite `saint-cloud.json`. Archive / sync.
