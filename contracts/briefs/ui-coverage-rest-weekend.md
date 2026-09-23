# Brief — agent UI · libellé « au moins un week-end »

Le tech lead : **dictionnaire week-end**. Relis `contracts/domain/coverage-rest-weekend.md` (hors freeze UI = cette phrase) + `score-facts.md`. Core déjà sur la branche freeze / master.

Branche **`cursor/coverage-rest-weekend-ui-2843`** depuis master **après** land Core. **Ne merge pas** `master`.

**Ne pas toucher** Python, `contracts/`.

`web/src/release.ts` + `package.json` : **0.61.0**, note FR : `Au moins un week-end off / 14 j.`

## Comportement

- Titre kind `weekend_every_two_weeks` : **Au moins un week-end / 14 j.** (plus « Un week-end / 14 j. » si ça implique exactement un).
- Miss liste : **`{name} : aucun week-end complet off / 14 j.`** — plus « pas exactement un week-end off ».
- Radio wizard / freeze `wellbeing.md` : pas de nouveau contrôle. Le texte d’aide s’il dit « exactement un » → « au moins un ».

Build. `/planning` recap souhait every_two : titre + phrase miss. Barre **v0.61.0**.

**Process** : commit + push. Signal le SHA.
