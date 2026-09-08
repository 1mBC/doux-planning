# Brief — coller dans le chat **Core**

Le tech lead : **notes de cycle /10** (couverture, légal, contrat+indispo, wellbeing, rôles = somme d’écarts) + globale pondérée. File worker close (`master has wizard-polish landed` + observability @ `bb33f1a`). Relis `contracts/domain/score.md` + `cycle-recaps.md` (`score` dans le recap) — tu les suis, tu ne les modifies pas.

`git pull origin master` (doit être `bb33f1a` ou plus récent, et contenir ce brief) ; branche **`score/core` depuis `master`**.

Nouveau change OpenSpec **`cycle-score`**. Skills → **propose puis `/opsx-apply`**. Pas d’archive / sync. Pas de `/opsx-update` recaps / warn-fr / generate.

**Process** : tâches + pytest vert → **commit + push `score/core` toi-même**. Message : `feat(core): cycle score notes out of ten`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `saint-cloud.json`. **Pas** de HTTP.  
`SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` / `_attempt_key` / `generate_cycle` keep-best **inchangés**.

## Comportement

- `cycle_score(draft, result)` (ou champ `score` produit par `cycle_recap`) selon `score.md`.
- 5 notes 0–10 une décimale, `null` si pas de dénominateur. `global` = moyenne poids 3 / 3 / 2 / 1.5 / 0.5.
- Couverture : `empty_post` / postes requis (même boucle slices).
- Légal : cellules `legal_rows` only.
- Contrat : moyenne (heures par fiche) + (cellules `indispo` si présentes).
- Wellbeing : `10 * held / total` ; null si total 0.
- Rôles : `10 * (1 − Σ(level−post) / Σ max(0, level−1))`.
- Exemple **92** (ne pas réécrire le snapshot).

## Tests

Couverture 10 si 0 vide et postes_requis > 0. Légal 10 si toutes cellules ok. Contrat : fiche pile contrat → 10 ; indispo cassée baisse la note. Wellbeing null si aucun souhait. Rôles 10 si tous les shifts au niveau. `generate_cycle` déterministe inchangé (`_attempt_key` même tuple). Pytest engine / recap / board verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core score pushed @ <sha>`
