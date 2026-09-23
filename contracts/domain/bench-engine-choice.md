# Choix de moteur du banc

Freeze **Infra** + **UI**. Pas de Core.

Gagne sur `bench.md` pour le moteur **courant du banc**, et sur `admin.md` pour le **repli** de `live_engine_ref`.  
Les deux choix restent **deux lignes**. `engines.md` : `core-5` = `engine.py`, plus un fichier.  
`data/bench/VERSION` **supprimé**. Personne ne le lit.

## Liste

`list_engine_refs()` est la liste, ordre du registre. Dernier nom = repli du banc.  
Pas de table catalogue. Ajouter ou retirer un moteur = un change qui édite le registre.

## Persist

Table **`bench_engine`**, une ligne. Colonnes : `id` entier clé primaire, `engine_ref` texte nullable.  
Alembic après `20260922_0019`. Pas de backfill. Pas une colonne de `live_engine`.

Même règle pour `bench_engine` et pour `live_engine` :

- ligne absente, `null`, vide, ou nom hors `list_engine_refs()` → écrire `list_engine_refs()[-1]`, retourner ce nom
- sinon retourner le nom stocké

La réécriture a lieu à la lecture. Un choix déjà valable ne bouge pas quand le registre gagne un nom.

## HTTP (admin)

```
PUT /v1/admin/bench/engine
{ "engine_ref": "core-2" }
```

200 :

```
{ "engine_ref": "core-2", "engine_refs": ["core-0", "…", "mix-0"] }
```

`engine_refs` du PUT = **registre seul**, ordre registre.  
Inconnu, vide, ou type faux → 400 `Moteur inconnu.` La ligne précédente reste.  
Sans session 401. Non-admin 403 `Action réservée à l’admin.` Sans base 503.

`GET /v1/admin/bench/versions` : `engine_ref` = résolveur (plus `VERSION`).  
`engine_refs` de versions = registre ∪ extras des runs, ordre inchangé.  
`app_version` d'un run reste le moteur de **ce** run.

`POST /v1/admin/bench/run` :

| body `engine_ref` | jobs | choix stocké |
|---|---|---|
| absent ou `""` | résolveur | inchangé, sauf si le résolveur réécrit un nom invalide |
| dans le registre | ce nom | inchangé |
| hors registre | 400 `engine_ref inconnu` | inchangé |

`scope=gaps` ignore `engine_ref`. Un job par trou × chaque nom de `list_engine_refs()`.

Compare-chemin `GET /v1/admin/bench/compare/{category}/{dataset_id}/{search_effort}` = last-run du **résolveur**.  
`below_manuel` = last-run du **résolveur** seulement.  
`dataset` et `bank` = tous les `engine_ref`, inchangés.

## Moteur client

`GET` et `PUT /v1/admin/live-engine` inchangés dans leur forme.  
`engine_ref` du GET = résolveur **client** (plus `VERSION`).  
`PUT` invalide → 400 `Moteur inconnu.`, ligne précédente inchangée.  
`POST /v1/generate` (sync et worker) lance le résolveur client. Le choix banc ne le change pas.

## UI

Les deux pages Banc IA et Banc Manuels.  
`.bench-engine-select` : valeur = `engine_ref` du `GET /versions`.  
Changement → `PUT`. Succès : afficher ce nom. Échec : `detail`, la liste reste sur le choix effectif d'avant.  
Pas de souvenir local qui contredit le GET au chargement.

Lancer tout, une catégorie, ou une ligne : body `engine_ref` = le nom affiché.  
Compléter les trous : ne pas envoyer `engine_ref`.

Sélecteur admin du moteur client : valeur = `GET /v1/admin/live-engine` `engine_ref`. Changement → `PUT` existant. Pas de nom de moteur codé en dur. Les deux sélecteurs ne s'écrasent pas.

Pas de `web/src/release.ts`. Pas de version dans `web/package.json`.

## Tests

Infra : TestClient, `skipif` sans `DATABASE_URL`.  
UI : `npm run build`, puis le parcours dans le navigateur (choix, rechargement, les deux pages, corps des lancements, trous sans `engine_ref`).
