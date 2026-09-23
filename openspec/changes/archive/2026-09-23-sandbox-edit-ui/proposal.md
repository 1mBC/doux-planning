## Why

Le snapshot exemple est lisible, mais le restaurateur ne peut pas encore essayer un cran (heures, personne, échange) sans rescorer dans le front. L’API sandbox (enter / preview / commit / undo) est déjà figée — désormais avec `impact` + `current_score` / `trial_score` par proposition, `score` sur l’état, et retune = un essai à `start_minutes` / `end_minutes`. Il faut le mode édition par-dessus, sans recalculer.

## What Changes

- Ajouter le bouton français **Mode édition** : `POST /v1/sandbox/enter`, puis grille et warnings depuis l’état sandbox (`GET` / commit / undo), plus `GET /v1/examples/saint-cloud` pour les shifts édités. Afficher `score` du draft tel quel (plus petit = mieux), sans le recomposer.
- Overlay au clic d’un créneau occupé.
  - **Heures (`retune`)** : une ligne début et une ligne fin, chacune `−` / `+` (15 min). Chaque clic : `POST /v1/sandbox/preview` `{ gesture: retune, shift, start_minutes, end_minutes }` (heures **après** le pas). Afficher le seul `impact` (pas de bloc score). **Valider** : commit avec ces start/end.
  - **Replace / swap** : `POST /v1/sandbox/preview` `{ gesture, shift }` → liste `proposals` dans l’ordre `rank` du moteur. Titre swap : **jour puis heure**. Par ligne : `impact` seulement (pas de `delta`, pas la liste cycle, pas de `current_score` / `trial_score` affichés). `role_fit` du créneau cliqué en vert/rouge. Commit puis remplacement du draft.
  - **Fill (case vide)** : en édition, clic sur une case `rest` ouvre un overlay fill (pas les 3 gestes occupés). Ouverture : `preview { gesture: fill, slot, start_minutes: null, end_minutes: null }`. Curseur ±15 après la 200, début/fin = `proposals[0].start_minutes/end_minutes` (pas d’heures inventées). Haut : personne de la ligne si elle est dans `proposals` + impact + Valider. Dessous : les autres, titre = nom, impact comme replace. Commit `{ gesture: fill, slot, employee_id, start_minutes, end_minutes }`. `weekday` = `monday`…`sunday` (`day_index % 7`). 409 : `detail` français, overlay ouvert, grille inchangée. History : « Créneau posé ».
  - Lignes contrat : ajouter `( % avant → % après )` d’affichage (`current_hours / contracted * 100`, `trial_hours / contracted * 100`, virgule française ; omettre si `contracted` = 0). Parser `score` / `current_score` / `trial_score` sans les montrer dans l’overlay.
  - Lignes `role_fit` (0 ou 1) : `better` vert « poste plus proche du niveau (−N) » (`N = current_gap - trial_gap`) ; `worse` rouge « surqualification +N » (`N = trial_gap - current_gap`). Liste vide = rien. N vient des champs API.
- Historique des crans = `history[]` **API** (recap : `shift`, `slot`, `employee_id`, `start_minutes`, `end_minutes`, `partner`, `impact` — pas de `current_score` sur un cran). `startEdit` / GET / commit / undo / discard affichent **cette** liste. Pas de journal React comme source. **Lecture** oublie le state local (le recap reste côté API). **Annuler** = `POST /v1/sandbox/undo` (dernier cran). 409 → message français, draft inchangé.
- **Tout annuler** si `history.length > 0` → `POST /v1/sandbox/discard`. 200 = grille reset + history `[]`. 404 → `detail` français. Lecture ne discard pas.
- Hors édition : écran exemple inchangé (stats, légal, souhaits). En édition : pas d’invention de `legal_rows` / `wish_rows` / `stats`.
- Aucune route nouvelle. Pas de score / generate / classer dans le front.

## Capabilities

### New Capabilities

- `sandbox-edit-ui`: mode édition lecture des previews moteur, commit, undo, discard, overlay, historique API.

### Modified Capabilities

- (aucune — `planning-ui` lecture seule reste le contrat de l’écran exemple)

## Impact

Uniquement `web/`. Proxy Vite `/v1` inchangé. `src/doux_planning/` hors `api/` non modifié ; `api/` seulement si le proxy casse (CORS). Contrats HTTP non modifiés.
