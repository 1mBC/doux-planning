# Ranger le banc (file 72)

Freeze **Infra + UI**. **Pas de Core.**  
Gagne sur le chrome `bench.md` UI (colonnes Lancer / Défi, exports, lancer par jeu).  
Suppose file 71 landé (`origin`, importés en base).

## Décisions figées

1. Plus de colonne **Lancer**. Plus de colonne **Défi**.
2. Sous le **nom du jeu** : bouton **`…`** → menu : 3 lancements, exporter ce jeu, **supprimer**.
3. Hover du texte du jeu (id + name) = `challenge_fr` ; si `comment` non null, le commentaire **en plus**.
4. **Exporter sous le Manuel** + **Exporter tout le banc** déménagent dans le bloc **Lancer** (en haut).
5. Filtre in-page **Tous | IA | Manuels** : **retiré** (file 73, `admin-ui-pass.md` **gagne**) — deux pages **Banc IA** / **Banc Manuels** à la place.
6. Supprimer = **ce jeu + tous ses résultats** (runs + jobs). Catalogue git **pas** réécrit : tombstone en base pour qu’un redeploy Railway ne le ramène pas.

## Infra

```
DELETE /v1/admin/bench/datasets/{category}/{dataset_id}   Bearer admin → 204
```

- Importé : DELETE row `bench_imported_datasets` + **tous** `bench_runs` + `bench_jobs` de ce couple.
- Catalogue : **n’efface pas** les fichiers. INSERT `bench_tombstones (category, dataset_id)` (PK couple). DELETE runs + jobs. 2ᵉ DELETE : 204 idempotent si déjà tombstoné (runs déjà vides).
- Inconnu (ni disque, ni import, ni tombstone) → 404 `Jeu introuvable.`
- 403 / 401 / 503 habituels.

Table `bench_tombstones` (Alembic) : `category`, `dataset_id`, `created_at`. PK `(category, dataset_id)`.

`GET /versions` / `list_datasets` / export / `all` / `category` / `gaps` / `_known_targets` : **exclure** les tombstones. Importés non tombstonés inchangés.

`origin` déjà émis (file 71). Pas d’autre clé.

## UI — `/admin/bench`

### Lancer (haut)

Bloc existant (sélecteur moteur, toutes catégories, par compute, trous, loader) **plus** les deux boutons d’export globaux (sous le Manuel / tout le banc), **dans ce bloc**.

### Derniers runs

File 72 avait un filtre client Tous | IA | Manuels. **File 73 le retire** : deux routes `/admin/bench` (catalogue) et `/admin/bench/manuels` (importés). Liste vide → « Aucun jeu. »

Tableau :

| Colonne | Contenu |
|---|---|
| Catégorie | inchangé |
| Jeu | `id` + `name` ; hover = défi (+ commentaire importé) ; sous le nom : **`…`** |
| Manuel | inchangé |
| `engine_ref`… | inchangé |

**Plus** de `th` Défi. **Plus** de `th` Lancer. **Plus** de pile LaunchButtons / Exporter dans la ligne.

Menu `…` (fermer au clic extérieur / Escape) :

1. Lancer Minimal
2. Lancer Optimisé
3. Lancer Maximal
4. Exporter ce jeu
5. Supprimer…

Lancer / exporter = **mêmes** POST/GET qu’aujourd’hui. Cuisine-only → afficher `detail`.

**Supprimer** : confirm `Supprimer ce jeu et tous ses résultats ?` Puis DELETE. 204 → retirer la ligne (refresh versions). Catalogue : disparaît malgré les fichiers (tombstone).

Hover : `title` natif **ou** tooltip existant type admin-tip. Pas de colonne dédiée.

Stats banc : **inchangée** (elle suit `/versions`, donc tombstones exclus). Pas de menu `…` là.

## Tests

Infra : DELETE importé → plus dans `/versions`, runs 0. DELETE `tight/halles` → plus listé, fichiers toujours là, 2ᵉ DELETE 204. Gaps ne requeue pas un tombstone. 404 id inconnu. Non-admin 403.

UI file 72 : tableau sans Défi/Lancer ; `…` ; exports globaux dans Lancer. Filtre in-page **file 73**.

## Hors freeze

Deux pages Banc IA / Manuels = file 73. Solve cuisine. Relance globale qui écrase. Éditer un jeu importé. Archive / sync.
