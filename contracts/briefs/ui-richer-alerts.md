# Brief — coller dans le chat **UI**

Le tech lead : polish **v0.16.0** — label **Contrat**, cellules orange, types / rôles, invite + QR. Infra a poussé **`origin/alerts/infra` @ `f8da381`**. Relis `contracts/domain/cycle-recaps.md` (section **UI**), `contracts/domain/wizard-ui.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/alerts/infra` ≠ `f8da381ff943b3fb37cb7a086eaebddce6826f77` → **stop**, remonte.  
`git pull origin master` (plus récent que `4f89424`, doit contenir ce brief) ; branche **`alerts/ui` depuis `master`**. **Ne merge pas** `alerts/infra` / `alerts/core` (Python). API à part : uvicorn Infra @ `f8da381`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` richer-alerts / cycle-recaps / weekend-rest. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `alerts/ui` toi-même**. Message : `feat(web): polish contrat orange invite QR v0.16.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.16.0`**, note FR : label Contrat, cellules orange, types / rôles, invite + QR.

## `/planning` company + `/exemple` (chrome)

- Warning `code === contract_hours` : pastille **Contrat** (pas « Souhait »). Les autres `souhait` restent « Souhait ». Ne change pas `severity` API.
- Tableaux légal + souhaits : cellule `ok: false` → **orange + gras** (la **cellule**, y compris `contrat`). Plus seulement la 1ʳᵉ case de la ligne.
- Titre wish : **Souhaits bien-être**.
- `message` **tel quel** (empty_post / max services déjà FR côté Core).
- Calculer / Mode édition **sous** Salle · Cuisine (pas sur la même ligne). Pas d’exports.

`/exemple` : même chrome ; **ne pas** réécrire le snapshot.

## Wizard

- **Types** : horloge et ±15 **même ligne** ; en-tête **STAFF après cette arrivée / ce départ** (pas répété dans les cellules — sac / erreur seuls) ; compteur N plus lisible. Persist / pire-cas / une ligne **inchangés**.
- **Rôles** : passe style (Nom + Niveau, stepper +/−). Pas de nouvelle clé.
- Case we : **retirer** le sous-texte « Chaque semaine ; un jour resto fermé compte. »
- Invite : **enlever** jeton + URL de chaque fiche. Bouton à côté du code entreprise **« Inviter mes employés »** → popup : copier `/register?company_code={code}` **et** QR de cette URL (`origin` + path). Tokens API **inchangés**, juste masqués. Petite lib QR dans `web/` OK. Pas de nouvelle route.

Seed / auth / salarié / live : inchangés hors chrome ci-dessus.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company : warning contrat = pastille Contrat ; cellule !ok orange+gras ; titre Souhaits bien-être ; Calculer sous les équipes. Types : ±15 collé à l’horloge, STAFF en en-tête seulement, N lisible, reload persisté. Rôles plus propres. Plus de jeton sous les fiches ; popup invite copie l’URL + montre un QR. Plus le sous-texte we. Exemple 92 sans session, chrome aligné, snapshot intact. Barre **v0.16.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI alerts pushed @ <sha>, v0.16.0`
