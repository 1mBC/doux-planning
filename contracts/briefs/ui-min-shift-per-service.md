# Brief — agent UI neuf (cloud) · change **min-shift-per-service**

Le tech lead : Équipe **un stepper par service**. Relis `contracts/domain/min-shift-per-service.md` UI + `wizard-ui.md` Équipe. **Gagne.** Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/min-shift-per-service-ui-2843`** depuis la freeze. **Ne merge pas** Python / `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Reste `web/`. **`0.54.0`**, note : `Min. créneau par service`.

**API** : GET peut encore renvoyer un **nombre** tant qu’Infra n’a pas fini. Parser objet **ou** nombre (nombre → 4 partout / remplir les services offerts à N). PATCH envoie l’objet. IronBee persist seulement si GET est déjà un objet ; sinon build + steppers locaux et **signale** le skip API.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): min shift stepper per service v0.54.0`. Signal le SHA.

## Comportement

- Équipe : un `Stepper` par service **offert** (`CONTEXT_SERVICES.filter`, PDJ → déj → dîner). Plus l’input unique.
- Réutiliser `Stepper` : `step={0.5}`, `min={0.5}`, défaut 4. **Même chrome** que rôles / types / overlay. Refactor générique seulement si un trou de API l’exige ; alors les autres call sites restent visuellement identiques.
- Service non offert : pas de stepper, pas de clé.
- `/exemple` inchangé.

## Vérif

Build. `/context` Équipe : steppers PDJ/déj/dîner selon services ; ±0,5 ; barre **v0.54.0**. Types / overlay steppers inchangés.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI min-shift-per-service pushed @ <sha>, v0.54.0`
