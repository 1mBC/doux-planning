# Brief — coller dans le chat **UI**

Le tech lead : steppers + table types + exports + **3 calculs** (poll Maximal). **Attends le land Infra** (`master has generate-jobs landed`). Relis `contracts/domain/wizard-ui.md` (stepper / table), `export-planning.md`, `generate-jobs.md` + `v1-generate.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/generate-jobs/infra` n’est **pas** le SHA du signal Infra → **stop**, remonte.  
`git pull origin master` (après land Infra, doit contenir ce brief) ; branche **`planning-polish/ui` depuis `master`**. **Ne merge pas** Python. API : uvicorn `master` **+ worker Compose** (maximal), proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` admin / export-planning. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `planning-polish/ui` toi-même**. Message : `feat(web): steppers types exports three generate v0.22.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.22.0`**, note FR : steppers, table types, exports soignés, trois calculs.

## Stepper

Un chrome compact **partout** (rôles, N / niveaux types, **overlay sandbox**) : label à part, `[−]` petit, **chiffre centré**, `[+]`. Plus de `.choice` nav sur les ±. ±15 types : **même** petit chrome.

## Services types

**Une `<table>` par feuille** (plus de `wave-line` cartes). Colonnes : **Type** (Arrivée | Sortie) · Heure (+ ±15) · N · Niveaux · **STAFF minimal resultant** (même sac qu’aujourd’hui) · poubelle. Persist / pire-cas / sous-onglets **inchangés**.

## Exports `/planning`

- **JPEG** : 2× pixels (`devicePixelRatio`), police lisible, qualité ≥ 0.95. Toujours les 2 semaines à l’écran.
- **XLSX** : **2 feuilles** Semaine A / B (ou Paire / Impaire). Grille type canvas : jours Lun–Dim, chaque jour DEBUT / FIN / NB HEURES. **Une ligne par service offert** (PDJ / DJ / Dîner), pas un Matin/Soir figé. Titre **Planning validé en date du :** + horodatage local d’export. Un peu de couleur (en-têtes, bandes). Lib `xlsx` OK. CSV / JSON **inchangés**.

## Calculer

Trois boutons si `ready[team]` : **Minimal** · **Optimisé** · **Maximal**. Loader overlay **≥ 1 s**, fermé quand le résultat est là (200 ou job `done`).  
Minimal / Optimisé → POST sync `search_effort`. Maximal → POST 202 puis **poll** `GET /v1/generate/jobs/{id}` (~1 s) jusqu’à `done` / `failed` (`detail` / `error` FR). Mode édition : calcul **off**. Pas salarié / `/exemple`.

## Vérif (IronBee ; sinon headless)

`npm run build`. Rôles + types + overlay : stepper compact, chiffre centré. Types : table + colonne Type + STAFF minimal resultant. Company : 3 boutons ; Minimal change/recalc (loader ≥ 1 s) ; Maximal 202 + poll → grille. XLSX 2 feuilles + titre daté + lignes services ; JPEG plus net. Barre **v0.22.0**. Exemple 92. Admin inchangé (env Railway).

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI planning-polish pushed @ <sha>, v0.22.0`
