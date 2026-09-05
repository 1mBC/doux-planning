# Brief — coller dans le chat **UI**

Le tech lead : **Services types une ligne** + recaps planning live + warning 11 h. Infra a poussé **`origin/recaps/infra` @ `3a3753d`**. Relis `contracts/domain/wizard-ui.md`, `contracts/domain/cycle-recaps.md`, `contracts/http/v1-generate.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/recaps/infra` ≠ `3a3753d799320f266fdc816623ed8ac7d0695a3f` → **stop**, remonte.  
`git pull origin master` (plus récent que `5f7435c`, doit contenir ce brief) ; branche **`recaps/ui` depuis `master`**. **Ne merge pas** `recaps/infra` / `recaps/core` (Python). API à part : uvicorn Infra @ `3a3753d`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` cycle-recaps / weekend-rest / seed. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `recaps/ui` toi-même**. Message : `feat(web): recaps live + types une ligne v0.15.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.15.0`**, note FR : types une ligne + indicateurs du planning calculé.

## Services types (`wizard-ui.md`)

Liste **chronologique** (arrivées et départs mélangés). **Une ligne** par événement. Ajouter = arrivée **ou** départ. Poubelle en bout de ligne.

Titres de colonnes (explicites) :

- Heure d’arrivée / de départ
- Nombre de personnes qui arrivent / qui partent
- Niveau minimal requis pour compléter le staff (arrivée) · à garder dans le staff (départ)
- **STAFF après** (plus « sac »)

Chaque **niveau de l’échelle** : compteur **+/−**. Arrivée = combien à ce min (N = somme). Départ = combien à garder (0 = pas de contrainte).  
Pire-cas + persist inchangés. Pas de `;`.

## `/planning` company

Cycle non null : parser `stats` / `legal_cols` / `legal_rows` / `wish_cols` / `wish_rows` (clé manquante → throw). **Ne pas** inventer les chiffres.

Hors édition, **comme l’exemple** :

- pastilles : shifts, vides, interdit, sous-rôle, heures %, souhaits tenus (`held` / `total`) ;
- tableau **Règles légales** (`legal_cols` + `legal_rows`, `text` tel quel) ;
- tableau **Souhaits** (`wish_cols` + `wish_rows` ; cellule `null` = vide). Pas de `we1j` / `weA` inventés.

**Mode édition** : cacher ces recaps (grille + warnings + historique seulement).  
Warnings : `message` **tel quel** (11 h a déjà les deux horloges côté Core).

`/exemple` : snapshot inchangé (vieilles cols OK). Seed / auth / salarié : inchangés hors parse cycles.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company : types — 2 arrivées + 1 départ sur des **lignes**, STAFF après, +/− par niveau, reload persisté. Calculer → pastilles + 2 tableaux ; Mode édition les cache ; warning 11 h montre les horloges si le moteur en pose. Exemple 92 sans session. Barre **v0.15.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI recaps pushed @ <sha>, v0.15.0`
