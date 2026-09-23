# Import resto → banc (file 71)

Freeze **Core (petit) + Infra + UI**.  
Gagne sur `bench.md` pour la **liste** des jeux (catalogue ∪ importés) et le chargement d’un jeu hors disque.  
File 70 (historique) déjà là : le popup part d’une ligne `/admin`. File 72 (chrome `…` / filtre) **après**.

Un restaurateur devient un **jeu de banc** : snapshot du contexte + oracle manuel optionnel + computes déjà publiés optionnels. Ça n’écrit **jamais** dans le resto (pas de `published_cycles` / sandbox / comptes mutés).

## Décisions figées

1. Catalogue git **inchangé** (50 fichiers). Les importés vivent **en base** (Railway écrase le disque).
2. `origin` : `catalogue` | `imported`. Catégorie des importés : **`imported`**.
3. Un import = **un** jeu (snapshot). Ré-importer le même resto = **un autre** jeu.
4. Cases **toutes ON** par défaut : salle, cuisine, dernier manuel publié, computes déjà publiés.
5. Note **/10** optionnelle → colonne **Manuel** du jeu si le planning à la main n’est pas complet (écrase `expected_score.global`).
6. Commentaire **optionnel** (texte libre) sur le jeu.
7. Lancer un importé = **salle only** (comme le banc actuel). Cuisine dans le snapshot, **pas** de solve cuisine (`bench.md` Hors freeze).

## Core

`load_bench_dataset` / `list_bench_datasets` / catalogue **intouchés**.

Extraire le solve déjà là :

```
run_bench_on(dataset: BenchDataset, effort, engine_ref: str | None = None) -> BenchOutcome
```

`run_bench(category, id, effort, engine_ref)` = `load_bench_dataset` puis `run_bench_on`. **Bit-à-bit** le même outcome qu’aujourd’hui sur un jeu catalogue.

```
bench_dataset_from_json(*, category, id, name, challenge_fr, context: dict, assignments: list) -> BenchDataset
```

- `context` = même forme que `context.json` (hours, roles, types, employees, `typical_week?`).
- `assignments` **peut être `[]`** (pas d’oracle). `_load_context` réutilisé (déjà multi-équipes).
- `invite_token` absent / ignoré.

`UnknownBenchDataset` inchangé. Tests : `run_bench_on(load_bench_dataset("tight","halles"), minimal)` ≡ `run_bench(...)`. Empty expected ne lève pas. Saint-Cloud / catalogue 50 **intouchés**. **Pas** de table, **pas** d’API.

## Infra persist (Alembic)

Table `bench_imported_datasets` :

```
category          # toujours "imported"
id                PK  (slug opaque court, ex. imp- + token_urlsafe 8)
name
challenge_fr
comment           nullable text
origin            # "imported"
source_restaurant_id  nullable
context           JSONB
expected          JSONB   # { assignments: [...] }  éventuellement vide
manual_score_override  Float nullable  # 0–10, 1 décimale
created_at
```

Runs / jobs : **mêmes** tables `bench_runs` / `bench_jobs` (`category=imported`, `dataset_id=id`).

## Preview (popup)

```
GET /v1/admin/restaurants/{restaurant_id}/import-preview   Bearer admin
```

200 :

```
{
  restaurant_id, restaurant_name, email,
  salle: {
    ready: bool,
    manuel_published: bool,
    computes_published: { minimal: bool, optimized: bool, maximal: bool }
  },
  cuisine: { …même forme },
  generate_count: int
}
```

`ready` = `team_ready`. `manuel_published` = slot `versions.manuel` non null. `computes_published.*` = slot non null. `generate_count` = nb de `generate_logs` de ce `restaurant_id`.  
404 / 403 / 401 / 503 comme file 70.

## POST import

```
POST /v1/admin/bench/import   Bearer admin
{
  restaurant_id: string,
  include_salle: bool,          # défaut true
  include_cuisine: bool,        # défaut true
  include_manuel: bool,         # défaut true
  include_runs: bool,           # défaut true
  manual_score: number | null,  # optionnel, omis = null
  comment: string | null        # optionnel, "" → null
}
```

Clés bool omises → `true`. `manual_score` fourni : nombre fini **0–10**, Infra `round(x, 1)`. Sinon / `null` → pas d’override. `comment` trim, vide → null.

400 `Champs invalides.` si : resto id faux ; **les deux** équipes à false ; `manual_score` hors [0, 10] / pas un nombre.  
404 resto inconnu. 403 admin.

200 :

```
{
  category: "imported",
  id, name, challenge_fr, origin: "imported",
  comment, manual_score_override,
  included: { salle, cuisine, manuel, runs }
}
```

### Snapshot contexte

Construire un `context` banc :

- `name` = `companies.name` trim, sinon email, sinon `Sans nom`.
- `challenge_fr` = commentaire si présent, sinon `Importé de {email}`.
- Hours / types / typical_week / ladders / employees : **filtrés** aux équipes cochées (l’autre équipe absente du JSON).
- Pas d’`invite_token`.

`id` unique. `source_restaurant_id` = l’id resto.

### Oracle manuel

Si `include_manuel` **et** au moins un `versions.manuel` non null parmi les équipes cochées : `expected.assignments` = union des assignments de ces slots (équipe filtrée).  
Sinon : `expected.assignments = []`.

Colonne Manuel (`GET /versions` `dataset.manual.global`) :

1. Si `manual_score_override` non null → **cette** valeur (même sans run).
2. Sinon si expected non vide → `evaluate` / `expected_score.global` (1er run, comme catalogue ; avant run : `null`).
3. Sinon → `null`.

À chaque `run_bench_on` persisté : si override, **écraser** `expected_score.global` (les autres notes d’oracle restent l’evaluate). Recalculer `deltas.global` vs cette globale.

### Computes déjà publiés (`include_runs`)

Seulement **salle** (banc salle-only), et seulement si `include_salle`.  
Pour chaque effort `minimal|optimized|maximal` dont le slot salle est non null : insérer un `bench_runs` :

- `app_version` / `engine_ref` = `slot.engine_ref` s’il existe, sinon `live_engine_ref` effectif
- `assignments` / `score` du slot
- `expected_score` : evaluate(expected) puis override globale si présent ; expected vide + override → `{ global: override, notes: 5× null, weights: … }`
- `deltas` vs cet expected
- `trace` null
- `duration_seconds` = slot ou `0`

Cuisine publiée : **pas** de `bench_runs` (jeux cuisine hors freeze).

## Liste / load / worker

`GET /v1/admin/bench/versions` : catalogue **puis** importés (`created_at` desc). Chaque dataset **ajoute** :

```
origin: "catalogue" | "imported"
comment: string | null
```

Catalogue : `origin=catalogue`, `comment=null`. Parser UI : clés **requises** après land 71 (file 72 s’en sert).

`load` d’un jeu `imported` : `bench_dataset_from_json` + row DB. Catalogue : disque.  
Worker `tick_bench_job` : si pas sur disque → DB, puis `run_bench_on`. Inconnu → failed comme aujourd’hui.

Export `scope=dataset` : context JSONB (pas le fichier). Compare : `run_id` existant inchangé.

`POST all` / `category` / `gaps` : les importés **comptent** (`category=imported` dans le dropdown catégories). Jeu **sans salle** (import cuisine-only) : POST `scope=dataset` → 400 `Ce jeu n’a pas de salle.` Gaps **saute** ces jeux.

## UI — popup depuis `/admin`

**Clic droit sur le nom du restaurant** (et bouton **Au banc** dans la colonne Planning, à côté de Voir) → popup.

Contenu :

1. En-tête : nom + email. GET preview.
2. Encadré **complet ?** (lecture) : par équipe, prêt / manuel publié / computes présents ; nb de generates.
3. Cases (défaut cochées) : **Salle**, **Cuisine**, **Dernier planning manuel publié**, **Computes déjà publiés**.
4. Champ optionnel **Note manuel /10** (number 0–10, pas 0,1 forcé côté UI : stepper existant **ou** input ; vide = pas d’override). Aide : « Si le planning à la main n’est pas complet. »
5. Encadré optionnel **Commentaire** (textarea).
6. Annuler / **Importer**.

POST puis toast **« Jeu importé. »** + lien vers `/admin/bench`. Erreur → `detail`. `restaurant_id` null → pas de popup, toast introuvable.

`/admin/bench` : les importés apparaissent (catégorie `imported`). Pas encore de `…` / filtre / delete (file 72).

## Tests

Core : `run_bench` halles minimal **identique** via `run_bench_on`. `bench_dataset_from_json` expected `[]` charge. Catalogue 50 inchangé.

Infra : preview ready flags. Import salle+manuel → versions liste `origin=imported`, `manual.global` = override si fourni. Import `include_runs` → last-run minimal présent sans POST run. Cuisine-only → 400 au POST dataset run. Non-admin 403. Resto 404.

UI : build. Clic droit resto ouvre popup cases ON ; import 200.

## Hors freeze

Delete / tombstone / filtre Tous|IA|Manuels / chrome `…` = file 72. Solve cuisine. Réécrire le git catalogue.
