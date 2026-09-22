# Brief — agent UI neuf (cloud) · change **admin-ui-pass** (file 73)

Le tech lead : repasse chrome admin. Relis `contracts/domain/admin-ui-pass.md` (**gagne**) + les sections UI de `admin-historique.md` / `bench-chrome.md` qu’il remplace. Tu ne modifies pas `contracts/`.

**Pas de Python.** HTTP impersonate / import / DELETE / `origin` sur `/versions` déjà là. Infra ajoute en parallèle SPA `/admin/bench/manuels` + `origin` sur POST run / export — envoie `origin` même si Infra lag (clé extra ignorée).

Instance **neuve**. Branche **`cursor/admin-ui-pass-ui-2843`** depuis **master**. **Ne merge pas** `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Reste `web/`. **`0.59.0`**, note : `Note colorée, actions, deux pages de banc`.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): admin note cell, actions column, two bench pages v0.59.0`. Signal le SHA.

## Comportement

### Historique `/admin`

- Colonnes : Heure, Email, **Actions**, Restaurant, Équipe, Effort, **Note**, Durée, Moteur. **Plus** Warnings, **plus** Planning, **plus** Voir / Au banc.
- **Actions** (après Email) : boutons `impersonate` | `exporter vers le banc`. `restaurant_id` null → disabled.
- `impersonate` = mint + copie + toast privée (file 70). Pas d’onglet auto. Plus de clic droit email.
- `exporter vers le banc` = popup import file 71. Plus de clic droit restaurant. Toast « Ouvrir le banc » → `/admin/bench/manuels`.
- **Note** : encart `.bench-cell` + bulle type `.bench-delta-bubble`. Texte `formatCycleNote`. Couleur `noteHue` / `noteTint` (recaps), **pas** `deltaBackground`. Clic → `/admin/planning/{id}`. Hover **de l’encart seulement** → `FactTip`. Retirer `tr:hover .admin-tip`.

### Banc

- Nav : **Banc IA** (`/admin/bench`) | **Banc Manuels** (`/admin/bench/manuels`). Plus de bouton **Banc**. Plus de Tous | IA | Manuels.
- Une `BenchPage`, `origin` d’après le path. `h1` = le nom de la page. Filtre client sur `dataset.origin`.
- Lancer all / category / gaps + exports `below_manuel` / `bank` : passer `origin` de la page.
- Banc Manuels : cacher le lanceur par catégorie.
- `Root` : matcher `/admin/bench/manuels` **avant** le fallback compare.

## Vérif

Build. Barre **v0.59.0**. `/admin` : Actions après Email, note cliquable, hover note only. `/admin/bench` sans importés ; `/admin/bench/manuels` sans catalogue. Stats banc intacte.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI admin-ui-pass pushed @ <sha>, v0.59.0`
