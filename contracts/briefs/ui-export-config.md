# Brief — coller dans le chat **UI**

Le tech lead : boutons **Exporter / Importer la config** à côté du seed. Infra a poussé **`origin/export-config/infra` @ `a6d4bd5`**. Landé @ **`f12299e`**. Relis `contracts/domain/export-config.md` (section **UI**) (tu le suis, tu ne le modifies pas).

`git fetch origin` ; si `origin/export-config/infra` ≠ `a6d4bd54a7381c89e998735d48b28a00160662f7` → **stop**, remonte.  
`git pull origin master` (plus récent que `abffd17`, doit contenir ce brief) ; branche **`export-config/ui` depuis `master`**. **Ne merge pas** Python. API : uvicorn Infra @ `a6d4bd5`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` seed / polish / snapshot. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `export-config/ui` toi-même**. Message : `feat(web): export import restaurant config v0.19.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.19.0`**, note FR : export / import config resto.

## `/context` company

Même `seed-row` que Saint-Cloud :

- **Exporter la config** → GET `/v1/context/export` → download JSON (`config-resto.json` ou `{name}-config.json`).
- **Importer une config** → fichier `.json` → confirm FR (remplace nom + rôles + équipe + souhaits + types + semaine ; casse les salariés liés ; pas de planning) → POST `/v1/context/import`. 200 = `adopt` comme le seed. `detail` si erreur.

`export_version === 1` requis (throw sinon). Pas de bouton ailleurs. Pas d’exports planning.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company : export télécharge un JSON v1 sans token ; import + confirm → wizard remplacé, reload persisté. Annuler le confirm = no-op. Exemple 92. Barre **v0.19.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI export-config pushed @ <sha>, v0.19.0`
