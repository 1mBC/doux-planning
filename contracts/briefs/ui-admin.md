# Brief — coller dans le chat **UI**

Le tech lead : table **admin** des generates — **en-têtes par jour**, **hover = warnings**. File admin Infra close (`master has admin landed` @ `bafd260`, Infra `ea6c607`). Relis `contracts/domain/admin.md` section **UI** (tu le suis, tu ne le modifies pas). `v1-auth.md` `me.admin`.

`git pull origin master` (plus récent que `bafd260`, doit contenir ce brief) ; branche **`admin/ui` depuis `master`**. **Ne merge pas** Python. API : uvicorn `master` (admin déjà landé), proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` export / polish. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `admin/ui` toi-même**. Message : `feat(web): admin generate table day headers hover v0.21.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.21.0`**, note FR : table admin des generates, en-têtes par jour, hover warnings.

## `/admin` + chrome

- `parseMe` : `admin: bool` obligatoire (`Me.admin`). Employee → `false`.
- Lien **Admin** dans `SessionChrome` **ssi** `me.admin`. Company non admin / salarié / anonyme : pas de lien.
- Route `/admin` : `me.admin` → `GET /v1/admin/generates` → table. Sinon message `Action réservée à l’admin.` **sans** fetch.
- Vide : « Aucun generate pour l’instant. »

## Table

Newest-first. **Un en-tête par jour** `Europe/Paris` (`created_at`) : `Dimanche 6 septembre 2026`. Pas de jour sans ligne. Colonnes : heure `HH:mm` Paris, email, restaurant, équipe (Salle / Cuisine).

**Hover** ligne (ou pastille N) = `warnings[].message` tels quels, un par ligne. Tableau vide de warnings → `aucun warning`. Pas de liste déroulée sous le tableau. Pas de bouton salarié / `/exemple` / `/planning`.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company `admin: true` : lien Admin ; `/admin` charge `{ entries }` ; 2 jours distincts → 2 en-têtes ; hover d’une ligne à warnings montre les `message`. Company non admin / salarié : pas de lien ; `/admin` = message réservé, **0** GET `/v1/admin/generates`. Liste vide = phrase vide. Barre **v0.21.0**. Exemple 92 inchangé.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI admin pushed @ <sha>, v0.21.0`
