# Choix de moteur du banc

Freeze **Infra** + **UI**. Pas de Core.

Gagne sur `bench.md` pour le moteur **courant du banc** (versions `engine_ref`, `POST` sans ref, compare-chemin, `below_manuel`).  
`admin.md` (`live_engine_ref`) **inchangé**. `engines.md` **inchangé**. Fichier `data/bench/VERSION` **inchangé** : il reste le repli du generate restaurant.

## Liste

`list_engine_refs()` est la liste, ordre du registre. Dernier nom = repli du banc.  
Pas de table catalogue. Ajouter ou retirer un moteur = un change qui édite le registre.

## Persist

Table **`bench_engine`**, une ligne. Colonnes : `id` entier clé primaire, `engine_ref` texte nullable.  
Alembic après `20260922_0019`. Pas de backfill. Pas une colonne de `live_engine`.

Résolveur :

- ligne absente, `null`, vide, ou nom hors `list_engine_refs()` → écrire `list_engine_refs()[-1]`, retourner ce nom
- sinon retourner le nom stocké

La réécriture a lieu à la lecture, pour que le rechargement voie le même nom.

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

## UI

Les deux pages Banc IA et Banc Manuels.  
`.bench-engine-select` : valeur = `engine_ref` du `GET /versions`.  
Changement → `PUT`. Succès : afficher ce nom. Échec : `detail`, la liste reste sur le choix effectif d'avant.  
Pas de souvenir local qui contredit le GET au chargement.

Lancer tout, une catégorie, ou une ligne : body `engine_ref` = le nom affiché.  
Compléter les trous : ne pas envoyer `engine_ref`.

Pas de `web/src/release.ts`. Pas de version dans `web/package.json`.

## Tests

Infra : TestClient, `skipif` sans `DATABASE_URL`.  
UI : `npm run build`, puis le parcours dans le navigateur (choix, rechargement, les deux pages, corps des lancements, trous sans `engine_ref`).
