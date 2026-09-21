# Brief — agent UI neuf (cloud) · change **manual-planning**

Le tech lead : cran **Manuel** sur `/planning`. Relis `contracts/domain/manual-planning.md` UI. **Gagne.** Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/manual-planning-ui-2843`** depuis la freeze. **Ne merge pas** Python / `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Reste `web/`. **`0.55.0`**, note : `Planning manuel`.

**API** : tant qu’Infra n’a pas mergé, GET cycles peut n’avoir que 3 clés → `manuel: null`. Enter manuel peut 409. Chrome + parser locaux ; persist IronBee seulement si enter 200 ; sinon **signale** le skip API. **Jamais** `postGenerate(..., "manuel")`. Banc : `BENCH_EFFORTS` reste 3.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): planning manuel slot v0.55.0`. Signal le SHA.

## Comportement

- Rangée 2 : **Manuel** après Maximal.
- Cran Manuel : pas (Re)Calculer ; « Entrer en mode édition » si `ready` même slot vide ; vide hors édition = « Pas encore publié » ; enter `{ search_effort: "manuel" }` ; **mêmes** Overlay / Fill / undo / discard / publish.
- Compute : inchangé.
- `/exemple` inchangé. Parser cycles : 4ᵉ clé optionnelle.

## Vérif

Build. `/planning` : 4 crans ; Manuel sans Recalculer ; ready → bouton édition. Barre **v0.55.0**. Banc 3 efforts. Overlay compute inchangé.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI manual-planning pushed @ <sha>, v0.55.0`
