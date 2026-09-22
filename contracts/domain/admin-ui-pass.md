# Repasse UI admin (file 73)

Freeze **Infra (petit) + UI**. **Pas de Core.**  
Gagne sur le chrome table de `admin-historique.md` / `admin.md` et sur le filtre banc de `bench-chrome.md`.  
HTTP impersonate, GET planning admin, popup import, DELETE jeu, `origin` sur `/versions` : **inchangés**.

Deux surfaces :

1. **Historique** — note = encart coloré du banc ; warnings au hover **de la note seulement** ; clic note = planning actuel ; colonne **Actions** après Email.
2. **Banc** — deux pages **Banc IA** / **Banc Manuels** à la place du filtre Tous | IA | Manuels.

## Décisions figées

1. Reprendre le chrome **cellule banc** (encart bordé, bulle colorée). La note historique est un **/10 absolu**, pas un delta vs Manuel → **ne pas** colorer avec `deltaBackground`. Teinte = `noteHue` déjà utilisé sur les recaps (`hue = 12 × note`).
2. Une seule zone de hover sur la ligne : **l’encart note**. Plus de tooltip au hover de la **ligne**, plus de colonne Warnings, plus de clic droit email / restaurant.
3. Clic sur la note = l’ancien **Voir** : `/admin/planning/{restaurant_id}` (planning **actuel**, lecture seule).
4. Colonne **Actions** juste après **Email**. Libellés **exacts** : `impersonate` | `exporter vers le banc`.
5. `impersonate` = le lien copiable file 70 (fenêtre privée, **pas** d’ouverture auto). `exporter vers le banc` = le popup import file 71.
6. Nav admin : **Historique des computes** | **Banc IA** | **Banc Manuels** | **Stats banc**. Plus de bouton unique **Banc**. Plus de filtre Tous | IA | Manuels dans la page.
7. `/admin/bench` = catalogue (`origin=catalogue`). `/admin/bench/manuels` = importés (`origin=imported`).
8. Lancer **toutes les catégories** / **par catégorie** / **trous** et les exports globaux **restent sur l’origine de la page** (Banc IA n’enqueue pas d’importés, et inversement).

## Historique — `/admin`

Ordre des colonnes :

| Colonne | Contenu |
|---|---|
| Heure | inchangé |
| Email | texte seul — **plus** de `onContextMenu` |
| **Actions** | `impersonate` \| `exporter vers le banc` |
| Restaurant | texte seul — **plus** de `onContextMenu` |
| Équipe | inchangé |
| Effort | inchangé |
| **Note** | encart (voir ci-dessous) |
| Durée | inchangé |
| Moteur | inchangé |

**Plus** de colonnes **Warnings** et **Planning**. **Plus** de boutons Voir / Au banc.

### Note (encart)

Même chrome visuel que la cellule banc (`.bench-cell` + bulle type `.bench-delta-bubble`) :

- Texte = `formatCycleNote(score_global)` (`8,4` / `—`).
- Fond / bordure de la bulle = `noteHue` / `noteTint` des recaps (`cycleRecaps.tsx`). Extraire un helper exportable **ou** recopier `hsl(12 * note, …)`. **Interdit** : `deltaBackground` (échelle vs Manuel, clamp \|Δ\|=1).
- `score_global` null : encart sans teinte, texte `—`.
- **Clic** (si `restaurant_id` non null) → `go("/admin/planning/" + restaurant_id)`. Sinon bouton inactif (pas de navigation).
- **Hover de l’encart seulement** → liste `FactTip` existante (cartes facts). `facts=[]` → `aucun warning`. **Pas** de `title` natif en plus. **Pas** de `.admin-table tbody tr:hover .admin-tip`.

### Actions

Deux boutons `choice`, `restaurant_id` null → les deux **disabled** (pas de POST).

- **`impersonate`** : `POST /v1/admin/impersonate` `{ restaurant_id }`, copie `url`, toast **« Lien copié — ouvre-le en navigation privée. »** Échec → `detail`. **Jamais** `window.open`.
- **`exporter vers le banc`** : ouvre le popup import **inchangé** (preview, 4 cases, note /10 optionnelle, commentaire, Importer).

Toast post-import : **« Jeu importé. »** + action **« Ouvrir le banc »** → **`/admin/bench/manuels`** (plus `/admin/bench`).

Sélecteur moteur client, `/admin/planning/{id}`, `/impersonate/{token}` : **inchangés**.

## Banc — deux pages

### Routes SPA

| Path | Page | `origin` |
|---|---|---|
| `/admin/bench` | Banc IA | `catalogue` |
| `/admin/bench/manuels` | Banc Manuels | `imported` |
| `/admin/bench/versions` | redirect → `/admin/bench` | — |
| `/admin/bench/stats` | Stats banc (combiné) | — |
| `/admin/bench/run/{id}` | compare run | — |
| `/admin/bench/{cat}/{id}/{effort}` | compare jeu | — |

Infra : ajouter **`/admin/bench/manuels`** à `SPA_PATHS` (comme `/admin/bench`). FastAPI sert `index.html` si `dist` présent.

UI `Root` : `/admin/bench/manuels` → **même** `BenchPage` avec `origin` imposé par le path. **Avant** le fallback compare. `parseBenchComparePath` ne matche pas (un seul segment).

### Nav

`AdminNavCurrent` : `"history" | "bench" | "bench-manuels" | "bench-stats"`.

Libellés : **Historique des computes** | **Banc IA** | **Banc Manuels** | **Stats banc**.  
Banc IA → `/admin/bench`. Banc Manuels → `/admin/bench/manuels`.

Pages run / compare : aucun des deux Banc n’est `disabled` (les deux cliquables).

### Page

**Même** tableau / `…` / Lancer / exports globaux que file 72, **sans** le groupe Tous | IA | Manuels.

- `h1` : **Banc IA** ou **Banc Manuels**.
- Datasets affichés = `dataset.origin ===` l’origine de la page. Vide → « Aucun jeu. »
- **Banc IA** : liste des catégories du lanceur = catégories **catalogue** présentes (pas `imported`).
- **Banc Manuels** : une seule catégorie `imported` → **cacher** la rangée « par catégorie » ; « Toutes les catégories » lance tous les importés.

### Lancer / export scopés

UI envoie **toujours** `origin` de la page sur :

```
POST /v1/admin/bench/run   body + origin   pour scope = all | category | gaps
GET  /v1/admin/bench/export?scope=below_manuel|bank&origin=
```

`scope=dataset` (menu `…` / un jeu) : **pas** besoin d’`origin` (le couple identifie le jeu).

## Infra HTTP

`origin` optionnel : `"catalogue"` | `"imported"`.

- Absent / `null` / `""` → **toutes** les origines (compat).
- Autre valeur → 400 `Champs invalides.`

### `POST /v1/admin/bench/run`

Body peut contenir `origin`. Filtre les cibles de `scope=all`, `scope=category`, `scope=gaps` (`_known_targets` / `_gap_targets`) :

- `catalogue` → jeux dont `origin=catalogue` (pas `category=imported`).
- `imported` → jeux `origin=imported`.
- `scope=dataset` : `origin` **ignoré** s’il est présent.
- `scope=category` + `origin` qui ne recouvre pas cette catégorie → liste vide, **pas** 400 (202 `total: 0` ou sync vide selon le chemin actuel).
- Cuisine-only importé : toujours 400 `Ce jeu n’a pas de salle.` au dataset ; exclus des all/gaps comme aujourd’hui.

Tombstones toujours exclus.

### `GET /v1/admin/bench/export`

Query `origin` optionnelle, **même** sémantique, pour `scope=below_manuel` et `scope=bank`. `scope=dataset` : `origin` ignoré.

`GET /versions` **inchangé** (la page filtre côté client).

Pas d’Alembic. Pas de Core.

## Tests

Infra (`skipif` sans `DATABASE_URL`) :

- SPA `/admin/bench/manuels` → `index.html` si `dist` (skip sinon).
- POST `scope=all` `origin=catalogue` n’enqueue **aucun** `category=imported` (après un import).
- POST `scope=all` `origin=imported` n’enqueue **aucun** jeu catalogue.
- POST `scope=gaps` `origin=catalogue` : pas de job importé.
- `origin` absent : all/gaps se comporte comme aujourd’hui (les deux origines).
- `origin=nope` → 400 `Champs invalides.`
- Export `scope=bank&origin=catalogue` : aucun dataset `imported`.
- Non-admin 403 inchangé.

UI : `npm run build`. Barre **v0.59.0**. Historique : pas de colonnes Warnings / Planning ; Actions après Email ; hover note seulement ; clic note → planning. Nav : Banc IA + Banc Manuels, plus de filtre dans la page. Banc IA n’affiche pas les importés.

## Hors freeze

Solve cuisine. Stats banc séparées IA / manuels. Éditer un jeu importé. Un moteur par resto. Archive / sync.
