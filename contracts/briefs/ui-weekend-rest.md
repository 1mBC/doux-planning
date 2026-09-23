# Brief — coller dans le chat **UI**

Le tech lead : case **repos we** + wizard **Services en premier** + **Services types**. Infra a poussé **`origin/weekend-rest/infra` @ `8b66525`**. Relis `contracts/domain/wizard-ui.md`, `contracts/domain/wellbeing.md`, `contracts/http/v1-context.md`, `contracts/http/v1-me-planning.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/weekend-rest/infra` ≠ `8b6652598ca4a52466fbe8a618057e19d6eb7c34` → **stop**, remonte.  
`git pull origin master` (plus récent que `37e3398`, doit contenir ce brief) ; branche **`weekend-rest/ui` depuis `master`**. **Ne merge pas** `weekend-rest/infra` / `weekend-rest/core` (Python). API à part : uvicorn sur le checkout Infra @ `8b66525`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` weekend-rest-day / wellbeing / seed. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `weekend-rest/ui` toi-même**. Message : `feat(web): weekend rest + Services-first types v0.14.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.14.0`**, note FR : case repos we + Services en premier + Services types.

## Comportement

Tout est dans `wizard-ui.md`. En court :

- Onglets : **Services → Rôles → Équipe → Souhaits → Services types → Semaine type**.
- Décocher un service → warning FR puis **purge** (types, semaine, indispos, `max_services`) des **deux** équipes. PATCH nettoyé. Service non offert **invisible** (plus de fallback les 3).
- Souhaits : case **« Au moins un repos samedi ou dimanche »** (`weekend_rest_day`), **à côté** de la radio we (cumulable). Max services = seulement les services offerts.
- `/planning` salarié : kind `weekend_rest_day` → même libellé, tenu / non tenu. Types TS : bool **requis**.
- **Services types** : sous-onglets par service offert ; **Ajouter un type** en bas. Vagues : pickers échelle, sac affiché, pire-cas → `remaining_post_levels` (exemples du freeze). Pas de `;`.

Seed, exemple 92, Calculer / live / auth : inchangés hors ce qui précède.

## Vérif (IronBee ; sinon headless)

`npm run build`. Company : Services d’abord ; décocher petit-déj après types → warning + plus de PDJ nulle part ; case repos we persistée au reload ; Services types (2 arrivées + 1 départ, sac = exemples du freeze) ; salarié `/planning` lit le wish. Exemple 92 sans session. Barre **v0.14.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI weekend-rest pushed @ <sha>, v0.14.0`
