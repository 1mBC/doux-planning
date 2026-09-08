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
  resumes: { mêmes clés: string | null }                   # FR ; `\n` si deux lignes (occupation)
  global: float | null
  weights: { couverture: 3, legal: 3, contrat: 2, wellbeing: 1.5, roles: 0.5 }
}
```

Toujours émettre les 5 clés de `notes` **et** les 5 de `resumes`.  
`notes.*` `null` = axe omis (pas de dénominateur) → `resumes.*` `null`.  
`global` = moyenne **pondérée** des notes non null ; `null` si aucune note. Pas de `resumes.global`.  
Arrondi : `round(x, 1)` Python, clamp `[0, 10]`.  
`weights` = constantes (mémoire). **Pas** d’UI / PATCH restaurateur dans cette tranche.

Clé JSON `contrat` **inchangée**. Libellé UI : **Occupation**.

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

**Note /10 inchangée** — somme des écarts, **pas** le compteur `below_role` :

```
ecarts   = Σ (level_fiche − post_level)     # _overqualification
plafond  = Σ max(0, level_fiche − 1)        # par shift
note     = 10 × (1 − ecarts / plafond)
```

`plafond == 0` (pas de shift, ou tous niveau 1) → `roles` null.

## Résumés (`resumes`)

`null` si la note est `null`. Heures = `_hours_label` (`29h` / `11h30`). Entiers pour les comptes.

- couverture : `{tenus} / {requis} postes tenus`
- legal : `{ok} / {n} règles tenues`
- contrat : parties présentes, **chaque partie sur sa ligne** (`\n`, plus de ` · `)
  - heures : `{h_posées} occupées / {h_contrat} contrat`  
    `h_posées` / `h_contrat` = `_hours_label` de `stats.hours.assigned` / `contracted` (14 j.)  
    ex. `58h occupées / 70h contrat`
  - indispo : `{ok} / {n} indispos tenues` (**ligne suivante** si les heures sont là)
- wellbeing : `{held} / {total} souhaits tenus`
- roles : `{N} affectés · {k} poste en sous-rôle / {N}`  
  `N` = `stats.assignments` (prises de poste) ; `k` = `stats.below_role`  
  Le résumé **n’est pas** la formule de la note (écart / plafond).

## Globale

```
global = Σ (poids × note) / Σ poids des axes non null
```

Poids ci-dessus. Axe `null` : exclu du dénominateur.

## UI (cette tranche)

Chrome seulement — **pas** de 2ᵉ formule.

- Rangée notes **au-dessus** de la grille (`/planning` company **et** `/exemple`).
- **Globale en premier à gauche.** Cadre **contrasté** vs les 5 axes : bordure plus épaisse, fond un cran plus saturé, même teinte HSL. Pas de résumé sous la globale.
- Libellés : Occupation / Couverture / Légal / Bien-être / Rôles / Globale, tous `/10`.
- Sous chaque pastille d’axe : `resumes[clé]` tel quel, **respecter les `\n`** (`white-space: pre-line`).
- **Jauge horizontale** sous le chiffre (5 axes + globale) : remplissage `note / 10`, même teinte `hue = 12 × note`. `null` → jauge vide, neutre.
- Couleur linéaire 0→10 : HSL `hue = 12 × note`. Pas de buckets.
- Pas de cartes `CycleStats` / `Stats`. Tableaux légal / souhaits **sous** la grille.

## Tests

- Notes /10 **inchangées** (occupation ×2, rôles = écart / plafond).
- `resumes.contrat` : `occupées` + `contrat` ; indispos sur une **deuxième** ligne (`\n`).
- `resumes.roles` : `affectés` + `sous-rôle` ; contient `below_role` et `assignments`.
- Keep-best inchangé. Exemple **92**.

## Hors freeze

Keep-best / `_attempt_key`. Poids éditables. Bench admin. Rewrite `saint-cloud.json`. Archive / sync.
