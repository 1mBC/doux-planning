# Brief — coller dans le chat **UI**

Le tech lead : loader Banc **sous « Lancer »**, plus d’overlay / flou. File 44 close (`master @ eba8c09`). Relis **`contracts/domain/bench.md`** UI (Loader inline).

`git pull origin master` ; branche **`bench-loader/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync. **Pas de Core / Infra.**

**Process** : tâches + `npm run build` vert → **commit + push `bench-loader/ui` toi-même**. Message : `feat(web): bench loader inline under Lancer v0.40.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.40.0`**, note FR : banc, loader sous Lancer, page lisible.

## Comportement

- % + temps max restant : **dans** la section Lancer, **juste sous** le `h2`. Plus de `calc-overlay` sur `/admin/bench`.
- Tableau, recap, export **cliquables** pendant le batch. Overlay planning resto **inchangé**.
- Poll / `batches/active` / gaps **inchangés**.

## Vérif

Build. `/admin/bench` avec batch actif : barre sous Lancer, **pas** de voile blanc. Barre **v0.40.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-loader pushed @ <sha>, v0.40.0`
