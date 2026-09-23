# Brief — coller dans le chat **UI**

Le tech lead : `/exemple` lit le snapshot **rafraîchi** (FR + wish live). Infra a poussé **`origin/snapshot/infra` @ `0ccb61a`**. Landé @ **`0206611`** (`master has snapshot landed` Infra). Relis `contracts/domain/exemple-snapshot.md` (section **UI**) et `contracts/http/v1-examples.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/snapshot/infra` ≠ `0ccb61a12f6916fb37d3233fb5638149eedf8b57` → **stop**, remonte.  
`git pull origin master` (plus récent que `9ffce6b`, doit contenir ce brief) ; branche **`snapshot/ui` depuis `master`**. **Ne merge pas** `snapshot/infra` / `snapshot/core` (Python). API à part : uvicorn Infra @ `0ccb61a`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de `/opsx-update` exemple-snapshot / warn-fr / cycle-recaps. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `snapshot/ui` toi-même**. Message : `feat(web): exemple snapshot FR wish live v0.17.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.17.0`**, note FR : exemple Saint-Cloud, alertes FR et souhaits live.

## `/exemple`

Parser le JSON tel quel. Pastilles **92 / 0 / 0 / 47 / 84 % / 10 / 12**. **17** warnings, `message` FR tel quel (pastille **Contrat** si `contract_hours`). Tableau wish = `wish_cols` live (contrat, indispo, consecutive_rest, max_evening, max_coupures…) — **zéro** `we1j` / `weA`. Diane `30h · 29h / 39h` orange. Théo midi lundi A 11h–16h. Chrome v0.16.0 inchangé (titre Souhaits bien-être, cellules `!ok` orange+gras).

OpenSpec : pin « 14 warnings » → **17**. Pas d’exports, pas de polish invite/types/we (file suivante).

## Vérif (IronBee ; sinon headless)

`npm run build`. `/exemple` sans session : 92, 17 alertes FR (« contrat », « pas deux repos »), 10/12, colonnes wish live, Diane orange, Théo 11h–16h. Company `/planning` inchangé hors parse. Barre **v0.17.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI snapshot pushed @ <sha>, v0.17.0`
