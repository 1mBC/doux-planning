# Brief — coller dans le chat **UI**

Le tech lead : **sélecteur moteur client** + **modèle sur la ligne d’horodatage**. File 53 close (`master has live-engine landed` @ `d24f706`). Relis **`contracts/domain/admin.md`** section UI (gagne) + `generate-versions.md` (ligne date · core).

`git fetch origin` ; si `origin/cursor/live-engine-api-d0df` ≠ `d24f706` → **stop**.  
`git pull origin master` ; branche **depuis `master`**. **Ne merge pas** Python. API uvicorn `master`, proxy `/v1` inchangé.

`/opsx-update build-planning-ui`. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push toi-même**. Message : `feat(web): admin live engine picker and compute model line v0.46.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.46.0`**, note FR : choix du moteur client et modèle sur l’horodatage.

## `/admin`

- `GET /v1/admin/live-engine` au chargement.
- En-tête : **« Moteur du planning client »** + sous-texte freeze + `<select>` des `engine_refs`.
- Change → PUT immédiat, select = 200.
- Liste vide de generates : le sélecteur **reste**. Colonne **Moteur** (`engine_ref` ou tiret).
- Company non admin / salarié : pas d’appel live-engine.

## `/planning` company

Ligne `.generated-at` : `formatGeneratedAt` **puis** ` · ` **puis** `cycle.engine_ref` s’il est là. Vieux cycle sans clé : date seule. Tiret si pas de `generated_at`. Durée = l’autre ligne, inchangée.  
**Pas** de select moteur sur `/planning`. Salarié : pas cette ligne (inchangé) — si `generated_at` y est déjà, **même** règle.

`parse` cycle : `engine_ref` string optionnel. Admin entry : `engine_ref` string | null (clé présente, null OK).

## Vérif (IronBee ; sinon headless)

Build. Admin : select affiche `core-5` ; changer `core-6` ; reload = `core-6`. Table : colonne moteur.  
Planning : après generate, ligne du type `15/09/2026 14:32:01 · core-6`. Vieux slot sans moteur : date seule. Barre **v0.46.0**. Banc inchangé.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI live-engine pushed @ <sha>, v0.46.0`
