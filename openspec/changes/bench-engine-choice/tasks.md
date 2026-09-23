# Tasks

## 1. Infra

- [ ] 1.1 Alembic après `20260922_0019` : table `bench_engine` (`id` entier clé primaire, `engine_ref` texte nullable). Ne pas modifier `live_engine`. Vérifier upgrade crée la table et downgrade la supprime.
- [ ] 1.2 Résolveur du choix banc : ligne absente, vide, ou hors `list_engine_refs()` → écrire le dernier nom du registre et le retourner. Nom présent dans le registre → le retourner tel quel. Vérifier les trois cas, y compris qu'une seconde lecture retrouve le nom réécrit.
- [ ] 1.3 `PUT /v1/admin/bench/engine` `{ "engine_ref" }`, admin seulement. 200 `{ "engine_ref", "engine_refs" }` avec `engine_refs` = le registre seul. Inconnu, vide ou mauvais type → 400 `Moteur inconnu.` et la ligne précédente inchangée. Sans session 401, non-admin 403, sans base 503. Vérifier avec TestClient (`skipif` sans `DATABASE_URL`).
- [ ] 1.4 `GET /v1/admin/bench/versions` : `engine_ref` = le résolveur, plus le fichier `VERSION`. `engine_refs` reste le registre plus les refs déjà en base, même ordre. Vérifier qu'un choix `core-2` stocké donne `engine_ref == "core-2"` même si `VERSION` vaut `core-5`.
- [ ] 1.5 `POST /v1/admin/bench/run` : `engine_ref` absent ou vide → jobs au nom du résolveur. Présent et valide → jobs à ce nom, choix stocké inchangé. Présent et invalide → 400 `engine_ref inconnu`, choix inchangé. `scope=gaps` ignore `engine_ref` et couvre chaque moteur du registre. Vérifier ces quatre cas.
- [ ] 1.6 Compare-chemin et export `below_manuel` utilisent le résolveur, pas `VERSION`. Export `dataset` et `bank` restent tous les `engine_ref`. Vérifier un choix `core-2` : compare et `below_manuel` lisent les last-run `core-2`.
- [ ] 1.7 Le generate restaurant ne lit pas `bench_engine`. Sans `live_engine` valable, il retombe sur `VERSION`. Vérifier qu'un choix banc `mix-0` laisse un generate sans `live_engine` sur le nom du fichier `VERSION`, et que les tests live-engine existants restent verts.

## 2. UI

- [ ] 2.1 Au changement de la liste `.bench-engine-select`, `PUT /v1/admin/bench/engine`. Succès : la valeur affichée est celle enregistrée. Échec : montrer le `detail`, la liste reste sur le choix effectif précédent. Au chargement, la valeur vient de `GET /versions` `engine_ref`, pas d'un souvenir local. Vérifier le parcours dans le navigateur sur Banc IA : choisir, recharger, le même moteur est sélectionné.
- [ ] 2.2 Banc Manuels affiche le même moteur. Lancer tout, une catégorie, ou une ligne envoie ce `engine_ref`. Compléter les trous n'envoie pas `engine_ref`. Vérifier ces lancements (le corps de la requête) et le Banc Manuels après un choix fait sur Banc IA.
- [ ] 2.3 `npm run build` vert. Ne pas modifier `web/src/release.ts` ni la version de `web/package.json`.
