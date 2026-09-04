# Brief — coller dans le chat **UI** (suite)

Le tech lead : Infra a exposé l’édition sandbox. Tes 4 décisions lecture seule tiennent pour l’écran exemple. Ce slice **ajoute** le mode édition par-dessus, sans rescorer.

**Lis (ne pas modifier) :** `contracts/http/v1-sandbox-edit.md` (et tranche 0 `contracts/http/v1-examples.md`). Conflit de forme → le contrat gagne.

**Mission :** nouveau change OpenSpec `sandbox-edit-ui`. Skills `.cursor/skills/openspec-*` → propose **puis** `/opsx-apply`. Contrat HTTP déjà figé.

## Produit

- Bouton français **« Mode édition »**. `POST /v1/sandbox/enter` puis la grille (et les warnings) viennent de `GET /v1/sandbox` / réponses commit-undo — **pas** de `GET /v1/examples/saint-cloud` pour les shifts édités.
- L’exemple public reste disponible hors édition (écran actuel). En édition : pas de `legal_rows` / `wish_rows` / `stats` sur le payload sandbox — ne les invente pas. Tableaux légal/souhaits : tu peux les cacher en édition ou les garder depuis le dernier exemple **en lecture**, sans les présenter comme le draft.
- Overlay (pop-up) au clic sur un **créneau occupé** (début, fin, ou total H) :
  1. Choisir le geste : changer les heures / attribuer une autre personne / échanger.
  2. Loader → `POST /v1/sandbox/preview` `{ gesture, shift }` (shift = égalité moteur, champs du contrat).
  3. Liste `proposals` dans l’ordre `rank` : personne ou nouvel horaire, warnings moteur, `delta` (ajoutés / retirés / inchangés). Messages moteur affichés tels quels.
  4. Clic une proposition → `POST /v1/sandbox/commit` avec les champs du geste (retune : start/end ; replace : employee_id ; swap : partner). Puis **remplacer** grille + warnings + historique par le body 200. Pas de websocket.
- Liste des crans `history` (geste). Annuler = `POST /v1/sandbox/undo` (un pop, le dernier). Pas d’annulation au milieu. 409 → message français, draft inchangé.
- Erreurs API : `detail` FastAPI en français.

## Interdit

- Scorer / générer / classer dans le front. Un seul score = preview/commit moteur.
- Auth, week vs cycle, publish, jobs.
- Modifier `src/doux_planning/` hors `api/` ; `api/` seulement si le proxy Vite casse (CORS).
- Modifier `contracts/`, l’archive V0, `preview-sandbox-edits`.
- `/opsx-archive`, `/opsx-sync`, commit.

Vérifier dans le navigateur (IronBee) : enter → overlay preview → commit met à jour la cellule → undo restaure. Proxy `/v1` → uvicorn inchangé.

Si une clé du contrat manque : stop.
