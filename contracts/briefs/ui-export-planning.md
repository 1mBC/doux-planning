# Brief — coller dans le chat **UI**

Le tech lead : menu **Exporter** le planning (JSON / CSV / XLSX / JPEG), **côté client**, équipe courante. File export-config close (`master has export-config landed` @ `9216c44`, v0.19.0). Relis `contracts/domain/export-planning.md` (tu le suis, tu ne le modifies pas).

`git pull origin master` (plus récent que `9216c44`, doit contenir ce brief) ; branche **`export-planning/ui` depuis `master`**. **Ne merge pas** Python. **Pas** de nouvelle route. API : uvicorn `master`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` export-config / polish. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `export-planning/ui` toi-même**. Message : `feat(web): export planning json csv xlsx jpeg v0.20.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.20.0`**, note FR : exporter le planning (JSON, CSV, XLSX, JPEG).

## `/planning` company

Menu **Exporter** (JSON / CSV / XLSX / JPEG) dans les actions sous Salle · Cuisine. Actif ssi cycle publié **et** pas en édition. Payload = cycle + fiches de **cette** équipe (sans tokens). Libs client OK. Pas de bouton salarié / `/exemple`.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company avec salle publiée : Exporter JSON s’ouvre / se télécharge (`export_version: 1`, `kind: planning`, 92-like assignments) ; CSV et XLSX ont nom + grille ; JPEG montre les 2 semaines. Cuisine null → menu off. Mode édition → off. Exemple 92. Barre **v0.20.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI export-planning pushed @ <sha>, v0.20.0`
