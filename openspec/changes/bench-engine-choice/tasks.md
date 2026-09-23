# Tasks

## 1. Core

- [x] 1.1 Supprimer `data/bench/VERSION` et `engine_ref()`. `generate_team` et `run_bench` sans moteur utilisent `list_engine_refs()[-1]`. `core-5` reste le nom de `engine.py` dans le registre. Vérifier qu'aucun module domaine ne lit le fichier, et que `pytest` du moteur est vert sans éditer `api/`, `web/` ni `contracts/`.

## 2. Infra

- [ ] 2.1 Alembic après `20260922_0019` : table `bench_engine` (`id` entier clé primaire, `engine_ref` texte nullable). Ne pas modifier le schéma de `live_engine`. Vérifier upgrade crée la table et downgrade la supprime.
- [ ] 2.2 Deux résolveurs, même règle. Ligne absente, vide, ou hors `list_engine_refs()` → écrire le dernier nom du registre et le retourner. Nom présent → le retourner tel quel. Un résolveur pour `bench_engine`, un pour `live_engine`. Vérifier les trois cas sur chaque table, y compris qu'une seconde lecture retrouve le nom réécrit. Aucun des deux ne lit `data/bench/VERSION`.
- [ ] 2.3 `PUT /v1/admin/bench/engine` `{ "engine_ref" }`, admin seulement. 200 `{ "engine_ref", "engine_refs" }` avec `engine_refs` = le registre seul. Inconnu, vide ou mauvais type → 400 `Moteur inconnu.` et la ligne précédente inchangée. Sans session 401, non-admin 403, sans base 503. Vérifier avec TestClient (`skipif` sans `DATABASE_URL`).
- [ ] 2.4 `GET /v1/admin/bench/versions` : `engine_ref` = le résolveur banc. `engine_refs` reste le registre plus les refs déjà en base, même ordre. Vérifier qu'un choix `core-2` stocké donne `engine_ref == "core-2"`.
- [ ] 2.5 `POST /v1/admin/bench/run` : `engine_ref` absent ou vide → jobs au nom du résolveur banc. Présent et valide → jobs à ce nom, choix stocké inchangé. Présent et invalide → 400 `engine_ref inconnu`, choix inchangé. `scope=gaps` ignore `engine_ref` et couvre chaque moteur du registre. Vérifier ces quatre cas.
- [ ] 2.6 Compare-chemin et export `below_manuel` utilisent le résolveur banc. Export `dataset` et `bank` restent tous les `engine_ref`. Vérifier un choix `core-2` : compare et `below_manuel` lisent les last-run `core-2`.
- [ ] 2.7 `GET /v1/admin/live-engine` et le generate restaurant utilisent le résolveur client. Un choix banc `mix-0` ne change pas le generate. Base client vide → generate sur le dernier du registre, et le GET admin montre ce nom. Un nom client hors liste est réécrit de la même façon. `PUT` invalide reste 400 `Moteur inconnu.` sans écraser la ligne. Vérifier que les tests live-engine existants passent avec ce repli, plus le fichier `VERSION` absent.

## 3. UI

- [ ] 3.1 Au changement de `.bench-engine-select`, `PUT /v1/admin/bench/engine`. Succès : la valeur affichée est celle enregistrée. Échec : montrer le `detail`, la liste reste sur le choix effectif précédent. Au chargement, la valeur vient de `GET /versions` `engine_ref`. Vérifier le parcours dans le navigateur sur Banc IA : choisir, recharger, le même moteur est sélectionné. Base vide : le dernier nom du registre est sélectionné, sans nom codé en dur.
- [ ] 3.2 Banc Manuels affiche le même moteur. Lancer tout, une catégorie, ou une ligne envoie ce `engine_ref`. Compléter les trous n'envoie pas `engine_ref`. Vérifier ces lancements (le corps de la requête) et le Banc Manuels après un choix fait sur Banc IA.
- [ ] 3.3 Le sélecteur admin du moteur client affiche `engine_ref` du `GET /v1/admin/live-engine` et enregistre encore par `PUT`. Base vide : le dernier nom du registre. Un choix client ne change pas la liste du banc, et l'inverse non plus. Vérifier les deux sélecteurs dans le navigateur.
- [ ] 3.4 `npm run build` vert. Ne pas modifier `web/src/release.ts` ni la version de `web/package.json`.
