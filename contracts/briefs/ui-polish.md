# Brief — coller dans le chat **UI**

Le tech lead : polish **v0.18.0** — invite URL **absolue**, types **hors tableur**, case we **colonne à part**. File snapshot close (`master has snapshot landed` @ `7e4547a`, v0.17.0). Relis `contracts/domain/wizard-ui.md` (tu le suis, tu ne le modifies pas).

`git pull origin master` (plus récent que `7e4547a`, doit contenir ce brief) ; branche **`polish/ui` depuis `master`**. **Ne merge pas** de Python. API : uvicorn sur `master` (proxy `/v1` inchangé).

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` exemple-snapshot / warn-fr / weekend-rest. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `polish/ui` toi-même**. Message : `feat(web): invite absolute URL types cards we column v0.18.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.18.0`**, note FR : URL d’invite complète, types en cartes, case we en colonne.

## Comportement

- **Invite** : popup affiche **et** copie `window.location.origin + /register?company_code={code}` (déjà `inviteRegisterUrl`). QR = cette même URL. Plus de path seul dans le presse-papiers.
- **Types** : plus de `<table class="wave-table">`. Chaque événement = une carte/ligne. Libellés courts une fois au-dessus. Horloge+±15, N, +/− niveaux, STAFF (sac seul), poubelle. Persist / pire-cas / ordre **inchangés**.
- **Souhaits** : `<th>` dédié **« Au moins un repos samedi ou dimanche »** ; la case n’est **plus** dans la cellule Week-end. JSON `weekend_rest_day` inchangé.

Pas d’exports, pas d’admin.

## Vérif (IronBee ; sinon headless)

`npm run build`. Invite : copier → URL qui commence par `http` + origin (collable sur téléphone) + QR. Types : plus de tableau Excel, 2 arrivées + 1 départ en cartes, reload persisté. Souhaits : case we dans sa colonne. Exemple 92. Barre **v0.18.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI polish pushed @ <sha>, v0.18.0`
