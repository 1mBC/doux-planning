# Brief — coller dans le chat **Core**

Le tech lead : **libellés resumes** — `occupées`, indispos à la ligne, rôles `affectés` / sous-rôle. **Notes /10 inchangées.** File score-chrome close (`master has score-chrome landed` @ `c978380` ou plus récent). Relis `contracts/domain/score.md` (section Résumés) — tu le suis, tu ne le modifies pas.

`git pull origin master` (doit contenir ce brief) ; branche **`score-gauges/core` depuis `master`**.

`/opsx-update` **`cycle-score`**. Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `score-gauges/core` toi-même**. Message : `feat(core): score resume labels occupées and roles`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `saint-cloud.json`. **Pas** de HTTP.  
Keep-best / `_attempt_key` / `SEARCH_*` / `generate_cycle` **inchangés**. Formules des 5 notes **inchangées**.

## Comportement

- `resumes.contrat` heures : `{label} occupées / {label} contrat` (`_hours_label` sur `stats.hours.assigned` / `contracted`).
- Indispos : **ligne suivante** (`\n`), plus de ` · `. Une seule partie → une seule ligne.
- `resumes.roles` : `{N} affectés · {k} poste en sous-rôle / {N}` avec `N = stats.assignments`, `k = stats.below_role`. **Pas** `écart / plafond` dans le texte. La note rôles reste l’écart.
- Autres resumes / notes / poids / globale : inchangés.

## Tests

`occupées` + `contrat` dans `resumes.contrat` ; `"\n"` entre heures et indispos quand les deux parties sont là.  
`resumes.roles` contient `affectés` et `sous-rôle` ; plus de préfixe `écart`.  
Notes numériques identiques au cas chrome (sur vs sous, pile C → 10, rôles écart). Pytest engine / recap verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core score-gauges pushed @ <sha>`
